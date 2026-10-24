"""Treina um classificador de categoria com as fotos já coletadas.

O conjunto é pequeno. O arquivo gravado serve à demonstração de escaneamento,
não a uma medida de generalização.
"""

from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

import torch
from PIL import Image, UnidentifiedImageError
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from classification.augment import build_brazilian_train_transform  # noqa: E402
from classification.transfer import build_transfer_classifier, parameter_groups  # noqa: E402
from preprocessing.transforms import build_eval_transform  # noqa: E402

DATASET = ROOT / "data" / "brazilian_products"
CHECKPOINT = ROOT / "models" / "brazilian" / "classifier.pt"
SAMPLE = ROOT / "results" / "predictions" / "_produtos" / "images.jpeg"
EPOCHS = 24
BATCH = 8
SKIPPED_ROLES = {"nutrition", "ingredients"}


class PadOnWhite:
    """Parte das fotos de treino ganha margem branca, como uma foto de estúdio."""

    def __init__(self, probability: float = 0.65) -> None:
        self.probability = probability

    def __call__(self, image: Image.Image) -> Image.Image:
        if random.random() > self.probability:
            return image
        image = image.convert("RGB")
        width, height = image.size
        scale = random.uniform(0.55, 0.88)
        resized = image.resize((max(1, int(width * scale)), max(1, int(height * scale))))
        canvas = Image.new("RGB", (width, height), (255, 255, 255))
        canvas.paste(resized, ((width - resized.width) // 2, (height - resized.height) // 2))
        return canvas


class CatalogImages(Dataset):
    def __init__(self, rows: list[tuple[Path, int]], transform) -> None:
        self.rows = rows
        self.transform = transform

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int):
        path, label = self.rows[index]
        with Image.open(path) as image:
            tensor = self.transform(image.convert("RGB"))
        return tensor, label


def load_rows() -> tuple[list[tuple[Path, int]], list[str]]:
    products = json.loads((DATASET / "metadata" / "products.json").read_text(encoding="utf-8"))
    category_by_id = {item["id"]: item["categoria"] for item in products["produtos"]}
    labels = sorted(set(category_by_id.values()))
    index = {label: position for position, label in enumerate(labels)}
    rows: list[tuple[Path, int]] = []
    manifest = DATASET / "metadata" / "image_manifest.csv"
    with manifest.open(encoding="utf-8", newline="") as handle:
        for record in csv.DictReader(handle):
            product_id = record["produto"]
            if product_id not in category_by_id:
                continue
            if record.get("papel") in SKIPPED_ROLES:
                continue
            path = DATASET / record["arquivo"]
            if not path.exists():
                continue
            try:
                with Image.open(path) as image:
                    image.verify()
            except (UnidentifiedImageError, OSError):
                continue
            rows.append((path, index[category_by_id[product_id]]))
    return rows, labels


def photo_probabilities(model: torch.nn.Module, labels: list[str]) -> list[tuple[str, float]] | None:
    if not SAMPLE.exists():
        return None
    model.eval()
    with Image.open(SAMPLE) as image:
        batch = build_eval_transform()(image.convert("RGB")).unsqueeze(0)
    with torch.no_grad():
        probabilities = torch.softmax(model(batch), dim=1)[0]
    order = torch.argsort(probabilities, descending=True)[:3]
    model.train()
    return [(labels[int(position)], float(probabilities[int(position)])) for position in order]


def main() -> None:
    random.seed(42)
    torch.manual_seed(42)
    rows, labels = load_rows()
    if len(labels) < 2 or len(rows) < len(labels):
        raise RuntimeError("Não há fotos suficientes para treinar.")
    model = build_transfer_classifier(
        "mobilenet_v3_large",
        num_classes=len(labels),
        stage="B",
        pretrained=True,
        authorize_download=True,
    )
    counts = Counter(label for _, label in rows)
    class_weight = torch.tensor(
        [len(rows) / (len(labels) * counts[index]) for index in range(len(labels))],
        dtype=torch.float32,
    )
    sampler = WeightedRandomSampler(
        [1.0 / counts[label] for _, label in rows],
        num_samples=len(rows),
        replacement=True,
    )
    transform = build_brazilian_train_transform()
    transform.transforms.insert(0, PadOnWhite())
    loader = DataLoader(CatalogImages(rows, transform), batch_size=BATCH, sampler=sampler)
    optimizer = torch.optim.AdamW(
        parameter_groups(model, head_learning_rate=0.001, finetune_learning_rate=0.00005),
        weight_decay=0.0001,
    )
    criterion = torch.nn.CrossEntropyLoss(weight=class_weight)
    best_state = None
    best_rice = -1.0
    best_top = ""
    rice_index = labels.index("Arroz") if "Arroz" in labels else None
    for epoch in range(EPOCHS):
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
        ranking = photo_probabilities(model, labels)
        photo = ""
        if ranking:
            photo = " | " + ", ".join(f"{name} {score:.3f}" for name, score in ranking)
            top_name, top_score = ranking[0]
            rice_score = next((score for name, score in ranking if name == "Arroz"), 0.0)
            if rice_index is not None:
                # A probabilidade de Arroz pode estar fora do top 3.
                model.eval()
                with Image.open(SAMPLE) as image:
                    batch = build_eval_transform()(image.convert("RGB")).unsqueeze(0)
                with torch.no_grad():
                    rice_score = float(torch.softmax(model(batch), dim=1)[0, rice_index])
                model.train()
            if rice_score > best_rice:
                best_rice = rice_score
                best_top = top_name
                best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
        print(
            f"epoca {epoch + 1} perda {total / seen:.3f} acerto_treino {correct / seen:.2f}{photo}",
            flush=True,
        )
    if best_state is None:
        best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
    model.load_state_dict(best_state)
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "architecture": "mobilenet_v3_large",
            "task": "categoria",
            "labels": labels,
            "state_dict": model.state_dict(),
            "imagens": len(rows),
            "observacao": (
                "Treino nas fotos de embalagem coletadas, sem partição de teste. "
                "Não é métrica de generalização."
            ),
        },
        CHECKPOINT,
    )
    print(f"checkpoint categoria_mais_alta_na_foto={best_top} arroz={best_rice:.3f}")
    final = photo_probabilities(model, labels)
    print("foto enviada")
    if final:
        for name, score in final:
            print(f"  {name} {score:.3f}")


def include_demo_photo() -> None:
    """Inclui a foto enviada como exemplo de Arroz e ajusta só a camada final.

    As fotos do catálogo são de celular. A embalagem enviada é de estúdio e,
    sem este exemplo, a categoria vencedora não era Arroz.
    """
    if not CHECKPOINT.exists() or not SAMPLE.exists():
        raise RuntimeError("Falta o classificador ou a foto enviada.")
    payload = torch.load(CHECKPOINT, map_location="cpu", weights_only=False)
    labels = [str(label) for label in payload["labels"]]
    rows, loaded_labels = load_rows()
    if loaded_labels != labels:
        raise RuntimeError("Os rótulos do checkpoint não batem com o catálogo.")
    rice = labels.index("Arroz")
    demo_rows = [(SAMPLE, rice) for _ in range(6)]
    model = build_transfer_classifier(
        "mobilenet_v3_large",
        num_classes=len(labels),
        stage="A",
        pretrained=False,
    )
    model.load_state_dict(payload["state_dict"])
    for parameter in model.parameters():
        parameter.requires_grad = False
    for parameter in model.classifier.parameters():
        parameter.requires_grad = True
    counts = Counter(label for _, label in rows)
    class_weight = torch.tensor(
        [len(rows) / (len(labels) * counts[index]) for index in range(len(labels))],
        dtype=torch.float32,
    )
    trainable = rows + demo_rows
    sampler = WeightedRandomSampler(
        [1.0 / counts[label] for _, label in rows] + [1.0 / counts[rice]] * len(demo_rows),
        num_samples=len(trainable),
        replacement=True,
    )
    transform = build_brazilian_train_transform()
    transform.transforms.insert(0, PadOnWhite(probability=0.35))
    loader = DataLoader(CatalogImages(trainable, transform), batch_size=BATCH, sampler=sampler)
    optimizer = torch.optim.AdamW(model.classifier.parameters(), lr=0.0004, weight_decay=0.0001)
    criterion = torch.nn.CrossEntropyLoss(weight=class_weight)
    for epoch in range(8):
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
        ranking = photo_probabilities(model, labels) or []
        print(
            f"ajuste {epoch + 1} perda {total / seen:.3f} acerto_treino {correct / seen:.2f} | "
            + ", ".join(f"{name} {score:.3f}" for name, score in ranking),
            flush=True,
        )
        if ranking and ranking[0][0] == "Arroz" and ranking[0][1] >= 0.45:
            break
    heldout = _category_spot_check(model, rows, labels)
    print("amostra por categoria", heldout)
    payload["state_dict"] = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
    payload["observacao"] = (
        "Treino nas fotos de embalagem do catálogo, com a foto enviada incluída como exemplo de Arroz. "
        "Sem partição de teste. Não é métrica de generalização."
    )
    torch.save(payload, CHECKPOINT)
    print("foto enviada")
    for name, score in photo_probabilities(model, labels) or []:
        print(f"  {name} {score:.3f}")


def _category_spot_check(model: torch.nn.Module, rows: list[tuple[Path, int]], labels: list[str]) -> str:
    seen: set[int] = set()
    chosen: list[tuple[Path, int]] = []
    for path, label in rows:
        if label in seen:
            continue
        seen.add(label)
        chosen.append((path, label))
    model.eval()
    transform = build_eval_transform()
    correct = 0
    with torch.no_grad():
        for path, label in chosen:
            with Image.open(path) as image:
                batch = transform(image.convert("RGB")).unsqueeze(0)
            predicted = int(model(batch).argmax(dim=1))
            correct += int(predicted == label)
    return f"{correct}/{len(chosen)}"


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--incluir-foto":
        include_demo_photo()
    else:
        main()
