"""Gera o resumo do dataset, a divisão e os dois experimentos de transfer learning.

A escolha do checkpoint usa o F1 macro da validação. O teste é calculado uma vez,
depois dessa escolha. A foto enviada pelo aplicativo não entra no experimento.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from classification.academic_train import predict_rows, run_stage  # noqa: E402
from datasets.academic_split import (  # noqa: E402
    academic_group_split,
    assert_no_group_leakage,
    category_counts,
    load_experiment_records,
)
from evaluation.classification import classification_scores  # noqa: E402

DATASET = ROOT / "data" / "brazilian_products"
SEED = 42
ARCHITECTURES = ("mobilenet_v3_large", "resnet18")


def main() -> None:
    records, excluded = load_experiment_records(DATASET)
    summary = build_summary(records, excluded)
    metrics = ROOT / "results" / "metrics"
    figures = ROOT / "results" / "figures"
    metrics.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    (metrics / "dataset_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    save_dataset_figures(records, figures)
    save_preprocess_examples(records, figures)

    split = academic_group_split(records, seed=SEED)
    assert_no_group_leakage(split)
    write_split(split)
    labels = sorted({record["categoria"] for record in records})
    rows_out = []
    for architecture in ARCHITECTURES:
        stage_a = run_stage(
            architecture=architecture,
            stage="A",
            rows_train=split["treino"],
            rows_val=split["validacao"],
            labels=labels,
            root=DATASET,
            seed=SEED,
        )
        measured_a = measure(stage_a["modelo"], labels, split, architecture, "A", stage_a)
        save_checkpoint(architecture, "A", labels, stage_a, measured_a)
        rows_out.append(measured_a)
        stage_b = run_stage(
            architecture=architecture,
            stage="B",
            rows_train=split["treino"],
            rows_val=split["validacao"],
            labels=labels,
            root=DATASET,
            seed=SEED,
            initial_state=stage_a["state_dict"],
            head_lr=0.0001,
            finetune_lr=0.0001,
        )
        measured_b = measure(stage_b["modelo"], labels, split, architecture, "B", stage_b)
        save_checkpoint(architecture, "B", labels, stage_b, measured_b)
        rows_out.append(measured_b)
        save_history_plot(architecture, stage_a["history"], stage_b["history"], figures)

    chosen = max(rows_out, key=lambda item: float(item["f1_validacao"]))
    source = ROOT / "models" / "brazilian" / f"{chosen['modelo']}_etapa_{chosen['etapa']}.pt"
    destination = ROOT / "models" / "brazilian" / "experiment_best.pt"
    destination.write_bytes(source.read_bytes())
    write_comparison(rows_out, metrics / "model_comparison.csv")
    (metrics / "model_comparison.json").write_text(json.dumps(rows_out, ensure_ascii=False, indent=2), encoding="utf-8")
    save_confusion(chosen, labels, figures)
    save_comparison_chart(rows_out, figures)
    print("escolhido", chosen["modelo"], chosen["etapa"], "f1_val", chosen["f1_validacao"], "f1_teste", chosen["f1"])


def build_summary(records: list[dict[str, str]], excluded: list[dict[str, str]]) -> dict[str, object]:
    widths, heights = [], []
    for record in records:
        with Image.open(DATASET / record["arquivo"]) as image:
            widths.append(image.width)
            heights.append(image.height)
    by_category = category_counts(records)
    by_product = Counter(record["produto"] for record in records)
    products_by_category: dict[str, set[str]] = defaultdict(set)
    for record in records:
        products_by_category[record["categoria"]].add(record["produto"])
    low = [category for category, count in by_category.items() if count < 4]
    return {
        "imagens_utilizaveis": len(records),
        "produtos": len(by_product),
        "categorias": len(by_category),
        "imagens_por_categoria": by_category,
        "produtos_por_categoria": {key: len(value) for key, value in sorted(products_by_category.items())},
        "imagens_por_produto": dict(sorted(by_product.items())),
        "resolucao_media": {
            "largura": round(sum(widths) / len(widths), 1),
            "altura": round(sum(heights) / len(heights), 1),
        },
        "imagens_excluidas": len(excluded),
        "motivos_exclusao": dict(Counter(item["motivo"] for item in excluded)),
        "categorias_com_baixa_representatividade": low,
        "criterio_baixa_representatividade": "menos de 4 imagens utilizáveis",
        "exclusao": (
            "Versos, tabelas nutricionais e ingredientes saíram do experimento. "
            "Os arquivos originais permanecem no manifesto."
        ),
    }


def save_preprocess_examples(records: list[dict[str, str]], figures: Path) -> None:
    from torchvision.transforms.functional import to_pil_image

    from classification.augment import build_brazilian_train_transform
    from preprocessing.transforms import IMAGENET_MEAN, IMAGENET_STD, build_eval_transform

    sample = records[0]
    with Image.open(DATASET / sample["arquivo"]) as image:
        original = image.convert("RGB")
        resized = build_eval_transform(normalize=False)(original)
        normalized = build_eval_transform()(original)
        augmented = build_brazilian_train_transform()(original)
    restored = normalized.clone()
    for channel, mean, std in zip(restored, IMAGENET_MEAN, IMAGENET_STD, strict=True):
        channel.mul_(std).add_(mean)
    panels = [
        ("Original", original),
        ("224×224", to_pil_image(resized)),
        ("Normalizada", to_pil_image(restored.clamp(0, 1))),
        ("Aumento", to_pil_image(_denormalize(augmented))),
    ]
    figure, axes = plt.subplots(1, 4, figsize=(10, 2.8))
    for axis, (title, panel) in zip(axes, panels, strict=True):
        axis.imshow(panel)
        axis.set_title(title, fontsize=9)
        axis.axis("off")
    figure.tight_layout()
    figure.savefig(figures / "preprocessamento.png", dpi=120)
    plt.close(figure)


def _denormalize(tensor):
    from preprocessing.transforms import IMAGENET_MEAN, IMAGENET_STD

    restored = tensor.clone()
    for channel, mean, std in zip(restored, IMAGENET_MEAN, IMAGENET_STD, strict=True):
        channel.mul_(std).add_(mean)
    return restored.clamp(0, 1)


def save_dataset_figures(records: list[dict[str, str]], figures: Path) -> None:
    by_category = category_counts(records)
    seen = defaultdict(set)
    for record in records:
        seen[record["categoria"]].add(record["produto"])
    products = {key: len(value) for key, value in seen.items()}
    _bar(list(by_category), list(by_category.values()), "Imagens por categoria", figures / "imagens_por_categoria.png")
    _bar(list(products), list(products.values()), "Produtos por categoria", figures / "produtos_por_categoria.png")
    categories = list(by_category)
    columns = min(4, len(categories))
    rows = (len(categories) + columns - 1) // columns
    figure, axes = plt.subplots(rows, columns, figsize=(columns * 2.4, rows * 2.6))
    flat = list(axes.ravel()) if hasattr(axes, "ravel") else [axes]
    for axis, category in zip(flat, categories, strict=False):
        sample = next(record for record in records if record["categoria"] == category)
        with Image.open(DATASET / sample["arquivo"]) as image:
            axis.imshow(image.convert("RGB"))
        axis.set_title(category, fontsize=8)
        axis.axis("off")
    for axis in flat[len(categories) :]:
        axis.axis("off")
    figure.tight_layout()
    figure.savefig(figures / "exemplos_dataset.png", dpi=120)
    plt.close(figure)


def write_split(split: dict[str, object]) -> None:
    destination = ROOT / "data" / "splits"
    destination.mkdir(parents=True, exist_ok=True)
    payload = {
        "split_id": split["split_id"],
        "seed": split["seed"],
        "estrategia": split["estrategia"],
        "limitacoes": split["limitacoes"],
        "quantidades": {name: len(split[name]) for name in ("treino", "validacao", "teste")},
        "categorias": {name: category_counts(split[name]) for name in ("treino", "validacao", "teste")},
    }
    (destination / "academico_s42.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    for name in ("treino", "validacao", "teste"):
        with (destination / f"academico_s42_{name}.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["produto", "arquivo", "categoria", "grupo_origem", "papel"],
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(split[name])


def measure(model, labels, split, architecture, stage, trained) -> dict[str, object]:
    true, pred, inference = predict_rows(model, DATASET, split["teste"], labels)
    if not true:
        return {
            "modelo": architecture,
            "etapa": stage,
            "accuracy": None,
            "precision": None,
            "recall": None,
            "f1": None,
            "f1_validacao": trained["f1_validacao"],
            "melhor_epoca": trained["melhor_epoca"],
            "segundos_treino": round(float(trained["segundos_treino"]), 1),
            "segundos_inferencia_media": round(inference, 4),
            "parametros_treinaveis": trained["parametros_treinaveis"],
            "categorias_no_teste": [],
            "categorias_ausentes_no_teste": labels,
            "matriz_confusao": [],
            "rotulos_matriz": labels,
            "historico": trained["history"],
            "observacao": "O teste não recebeu imagens.",
        }
    present_ids = sorted(set(true))
    observed = classification_scores(true, pred, labels=present_ids)
    full = classification_scores(true, pred, labels=list(range(len(labels))))
    present = {labels[index] for index in true}
    return {
        "modelo": architecture,
        "etapa": stage,
        "accuracy": observed["accuracy"],
        "precision": observed["precision_macro"],
        "recall": observed["recall_macro"],
        "f1": observed["f1_macro"],
        "f1_validacao": trained["f1_validacao"],
        "melhor_epoca": trained["melhor_epoca"],
        "segundos_treino": round(float(trained["segundos_treino"]), 1),
        "segundos_inferencia_media": round(inference, 4),
        "parametros_treinaveis": trained["parametros_treinaveis"],
        "categorias_no_teste": sorted(present),
        "categorias_ausentes_no_teste": [label for label in labels if label not in present],
        "matriz_confusao": full["confusion_matrix"],
        "rotulos_matriz": labels,
        "historico": trained["history"],
        "observacao": (
            "Accuracy, precision, recall e F1 macro consideram as categorias presentes no teste. "
            "A matriz usa todas as categorias do experimento. "
            "A seleção do checkpoint usou só a validação."
        ),
    }


def save_checkpoint(architecture, stage, labels, trained, measured) -> None:
    import torch

    path = ROOT / "models" / "brazilian" / f"{architecture}_etapa_{stage}.pt"
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "architecture": architecture,
            "task": "categoria",
            "stage": stage,
            "labels": labels,
            "state_dict": trained["state_dict"],
            "split_id": "academico-grupos-s42",
            "seed": SEED,
            "f1_validacao": trained["f1_validacao"],
            "f1_teste": measured["f1"],
            "observacao": "Checkpoint experimental. A seleção usou a validação, não a foto de demonstração.",
        },
        path,
    )


def write_comparison(rows: list[dict[str, object]], path: Path) -> None:
    fields = [
        "modelo",
        "etapa",
        "accuracy",
        "precision",
        "recall",
        "f1",
        "segundos_treino",
        "segundos_inferencia_media",
        "parametros_treinaveis",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def save_history_plot(architecture, history_a, history_b, figures: Path) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(9, 3.4))
    for history, name in ((history_a, "A"), (history_b, "B")):
        epochs = [item["epoca"] for item in history]
        axes[0].plot(epochs, [item["loss_treino"] for item in history], label=f"{name} treino")
        axes[0].plot(epochs, [item["loss_validacao"] for item in history], linestyle="--", label=f"{name} validação")
        axes[1].plot(epochs, [item["acuracia_treino"] for item in history], label=f"{name} treino")
        axes[1].plot(epochs, [item["acuracia_validacao"] for item in history], linestyle="--", label=f"{name} validação")
    axes[0].set_title("Loss")
    axes[1].set_title("Acurácia")
    axes[0].legend(fontsize=7)
    axes[1].legend(fontsize=7)
    figure.suptitle(architecture)
    figure.tight_layout()
    figure.savefig(figures / f"curvas_{architecture}.png", dpi=120)
    plt.close(figure)


def save_confusion(chosen: dict[str, object], labels: list[str], figures: Path) -> None:
    matrix = chosen["matriz_confusao"]
    names = chosen["rotulos_matriz"] or labels
    if not matrix:
        return
    figure, axis = plt.subplots(figsize=(6.5, 5.5))
    image = axis.imshow(matrix, cmap="Blues")
    axis.set_xticks(range(len(names)), names, rotation=45, ha="right", fontsize=7)
    axis.set_yticks(range(len(names)), names, fontsize=7)
    axis.set_xlabel("Previsto")
    axis.set_ylabel("Real")
    figure.colorbar(image, ax=axis)
    figure.tight_layout()
    figure.savefig(figures / "matriz_confusao_teste.png", dpi=120)
    plt.close(figure)


def save_comparison_chart(rows: list[dict[str, object]], figures: Path) -> None:
    names = [f"{row['modelo'].split('_')[0]}\n{row['etapa']}" for row in rows]
    values = [float(row["f1"] or 0) for row in rows]
    figure, axis = plt.subplots(figsize=(6.2, 3.4))
    axis.bar(names, values)
    axis.set_ylim(0, 1)
    axis.set_ylabel("F1 macro no teste")
    figure.tight_layout()
    figure.savefig(figures / "comparacao_modelos.png", dpi=120)
    plt.close(figure)


def _bar(labels: list[str], values: list[int], title: str, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(7.2, 3.6))
    axis.bar(labels, values)
    axis.set_title(title)
    axis.tick_params(axis="x", rotation=45, labelsize=8)
    figure.tight_layout()
    figure.savefig(path, dpi=120)
    plt.close(figure)


if __name__ == "__main__":
    main()
