"""Divisão acadêmica e formato dos tensores."""

from __future__ import annotations

from pathlib import Path

import torch
from PIL import Image

from classification.augment import build_brazilian_train_transform
from classification.candidates import load_checkpoint
from classification.transfer import build_transfer_classifier
from datasets.academic_split import academic_group_split, assert_no_group_leakage
from preprocessing.transforms import build_eval_transform


def _records() -> list[dict[str, str]]:
    rows = []
    for category, count in (("Arroz", 4), ("Café", 2), ("Sal", 1)):
        for index in range(count):
            rows.append(
                {
                    "produto": f"{category}{index}",
                    "arquivo": f"{category}/{index}.jpg",
                    "categoria": category,
                    "grupo_origem": f"{category}:{index}",
                    "papel": "front",
                }
            )
    return rows


def test_split_keeps_each_origin_group_in_one_part() -> None:
    split = academic_group_split(_records(), seed=42)
    assert_no_group_leakage(split)
    assert len(split["treino"]) + len(split["validacao"]) + len(split["teste"]) == 7
    assert any("Sal" in item for item in split["limitacoes"])
    groups = [item["grupo_origem"] for item in split["treino"] + split["validacao"] + split["teste"]]
    assert len(groups) == len(set(groups))


def test_eval_tensor_is_imagenet_sized() -> None:
    image = Image.new("RGB", (80, 120), (20, 40, 60))
    tensor = build_eval_transform()(image)
    assert tuple(tensor.shape) == (3, 224, 224)


def test_train_transform_matches_eval_tensor_shape() -> None:
    image = Image.new("RGB", (300, 200), (200, 180, 40))
    tensor = build_brazilian_train_transform()(image)
    assert tuple(tensor.shape) == (3, 224, 224)


def test_inference_probabilities_match_class_count() -> None:
    labels = ["Arroz", "Café", "Feijão"]
    model = build_transfer_classifier("mobilenet_v3_large", num_classes=len(labels), stage="A", pretrained=False)
    model.eval()
    with torch.no_grad():
        probabilities = torch.softmax(model(torch.zeros(1, 3, 224, 224)), dim=1)
    assert probabilities.shape == (1, 3)
    assert torch.allclose(probabilities.sum(dim=1), torch.ones(1), atol=1e-5)


def test_checkpoint_roundtrip_keeps_labels(tmp_path: Path) -> None:
    model = build_transfer_classifier("resnet18", num_classes=2, stage="A", pretrained=False)
    path = tmp_path / "modelo.pt"
    torch.save(
        {"architecture": "resnet18", "task": "categoria", "labels": ["A", "B"], "state_dict": model.state_dict()},
        path,
    )
    loaded = load_checkpoint(path)
    assert loaded is not None
    assert loaded["labels"] == ["A", "B"]
    restored = build_transfer_classifier("resnet18", num_classes=2, stage="A", pretrained=False)
    restored.load_state_dict(loaded["state_dict"])
    restored.eval()
