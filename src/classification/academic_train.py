"""Treino acadêmico com parada pela validação.

O conjunto de teste não escolhe checkpoint nem hiperparâmetro.
A fotografia de demonstração não participa desta seleção.
"""

from __future__ import annotations

import time
from pathlib import Path

import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset

from classification.augment import build_brazilian_train_transform
from classification.transfer import apply_stage, build_transfer_classifier, parameter_groups
from evaluation.classification import classification_scores
from preprocessing.transforms import build_eval_transform
from utils.seed import set_seed


class ImageRows(Dataset):
    def __init__(self, root: Path, rows: list[dict[str, str]], labels: dict[str, int], transform) -> None:
        self.root = root
        self.rows = rows
        self.labels = labels
        self.transform = transform

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int):
        record = self.rows[index]
        with Image.open(self.root / record["arquivo"]) as image:
            tensor = self.transform(image.convert("RGB"))
        return tensor, self.labels[record["categoria"]]


def run_stage(
    *,
    architecture: str,
    stage: str,
    rows_train: list[dict[str, str]],
    rows_val: list[dict[str, str]],
    labels: list[str],
    root: Path,
    seed: int,
    epochs: int = 20,
    batch_size: int = 8,
    patience: int = 5,
    head_lr: float = 0.001,
    finetune_lr: float = 0.0001,
    initial_state: dict | None = None,
) -> dict[str, object]:
    set_seed(seed)
    index = {label: position for position, label in enumerate(labels)}
    model = build_transfer_classifier(
        architecture,
        num_classes=len(labels),
        stage=stage,  # type: ignore[arg-type]
        pretrained=initial_state is None,
        authorize_download=True,
    )
    if initial_state is not None:
        model.load_state_dict(initial_state)
        apply_stage(model, architecture, stage)  # type: ignore[arg-type]
    train_loader = DataLoader(
        ImageRows(root, rows_train, index, build_brazilian_train_transform()),
        batch_size=batch_size,
        shuffle=True,
    )
    learning_rate = head_lr if stage == "A" else finetune_lr
    optimizer = torch.optim.AdamW(
        parameter_groups(model, head_learning_rate=head_lr, finetune_learning_rate=learning_rate),
        weight_decay=0.0001,
    )
    criterion = torch.nn.CrossEntropyLoss()
    best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
    best_f1 = -1.0
    best_epoch = 0
    wait = 0
    history: list[dict[str, float]] = []
    started = time.perf_counter()
    trainable = sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
    for epoch in range(1, epochs + 1):
        train_loss, train_acc = _train_epoch(model, train_loader, criterion, optimizer)
        val_loss, val_true, val_pred = _evaluate(model, root, rows_val, index)
        val_acc = float(sum(int(left == right) for left, right in zip(val_true, val_pred, strict=True)) / max(len(val_true), 1))
        val_f1 = float(classification_scores(val_true, val_pred)["f1_macro"]) if val_true else 0.0
        history.append(
            {
                "epoca": epoch,
                "loss_treino": train_loss,
                "acuracia_treino": train_acc,
                "loss_validacao": val_loss,
                "acuracia_validacao": val_acc,
                "f1_validacao": val_f1,
            }
        )
        print(
            f"{architecture} etapa {stage} epoca {epoch} "
            f"loss_treino {train_loss:.3f} acc_treino {train_acc:.3f} "
            f"loss_val {val_loss:.3f} acc_val {val_acc:.3f} f1_val {val_f1:.3f}",
            flush=True,
        )
        if val_f1 > best_f1:
            best_f1 = val_f1
            best_epoch = epoch
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
            wait = 0
        else:
            wait += 1
            if wait >= patience:
                print(f"parada antecipada na epoca {epoch}", flush=True)
                break
    elapsed = time.perf_counter() - started
    model.load_state_dict(best_state)
    return {
        "state_dict": best_state,
        "history": history,
        "melhor_epoca": best_epoch,
        "f1_validacao": best_f1,
        "segundos_treino": elapsed,
        "parametros_treinaveis": int(trainable),
        "modelo": model,
    }


def predict_rows(model: torch.nn.Module, root: Path, rows: list[dict[str, str]], labels: list[str]) -> tuple[list[int], list[int], float]:
    index = {label: position for position, label in enumerate(labels)}
    true, pred = [], []
    started = time.perf_counter()
    model.eval()
    transform = build_eval_transform()
    with torch.no_grad():
        for record in rows:
            with Image.open(root / record["arquivo"]) as image:
                batch = transform(image.convert("RGB")).unsqueeze(0)
            logits = model(batch)
            true.append(index[record["categoria"]])
            pred.append(int(logits.argmax(dim=1)))
    elapsed = time.perf_counter() - started
    mean_inference = elapsed / max(len(rows), 1)
    return true, pred, mean_inference


def _train_epoch(model, loader, criterion, optimizer) -> tuple[float, float]:
    model.train()
    total = 0.0
    correct = 0
    seen = 0
    for batch, target in loader:
        optimizer.zero_grad()
        logits = model(batch)
        loss = criterion(logits, target)
        loss.backward()
        optimizer.step()
        total += float(loss.detach()) * len(target)
        correct += int((logits.argmax(dim=1) == target).sum())
        seen += len(target)
    return total / max(seen, 1), correct / max(seen, 1)


def _evaluate(model, root: Path, rows: list[dict[str, str]], index: dict[str, int]) -> tuple[float, list[int], list[int]]:
    if not rows:
        return 0.0, [], []
    model.eval()
    transform = build_eval_transform()
    criterion = torch.nn.CrossEntropyLoss()
    total = 0.0
    true: list[int] = []
    pred: list[int] = []
    with torch.no_grad():
        for record in rows:
            with Image.open(root / record["arquivo"]) as image:
                batch = transform(image.convert("RGB")).unsqueeze(0)
            target = torch.tensor([index[record["categoria"]]])
            logits = model(batch)
            total += float(criterion(logits, target))
            true.append(int(target))
            pred.append(int(logits.argmax(dim=1)))
    model.train()
    return total / len(rows), true, pred
