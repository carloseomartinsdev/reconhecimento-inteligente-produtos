from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import torch
import torch.nn as nn

from classification.infer import predict_proba
from classification.models import build_classifier, count_parameters
from classification.train import train_classifier
from detection.yolo import load_local_yolo, train_detector, yolo_plan
from evaluation.classification import classification_scores
from evaluation.detection import (
    average_precision,
    detection_counts_at_threshold,
    iou_xyxy,
    mean_average_precision,
)
from evaluation.performance import file_size_bytes, measure_latency, parameter_bytes
from hybrid.pipeline import crop_hwc, fuse_scores, train_hybrid
from utils.device import get_device


def test_classification_scores_match_known_fixture() -> None:
    scores = classification_scores([0, 0, 1, 1], [0, 1, 1, 1], labels=[0, 1])
    assert scores["accuracy"] == 0.75
    assert scores["confusion_matrix"] == [[1, 1], [0, 2]]
    assert scores["precision_per_class"][0] == 1.0
    assert scores["recall_per_class"][0] == 0.5
    assert scores["precision_per_class"][1] == pytest.approx(2 / 3)


def test_average_precision_fixtures() -> None:
    ground_truth = [{"image_id": "img", "box": (0, 0, 10, 10)}]
    true_positive = [{"image_id": "img", "score": 0.9, "box": (0, 0, 10, 10)}]
    false_positive = [{"image_id": "img", "score": 0.9, "box": (30, 30, 40, 40)}]
    assert average_precision(true_positive, ground_truth) == 1.0
    assert average_precision(false_positive, ground_truth) == 0.0
    mixed = [
        {"image_id": "img", "score": 0.9, "box": (30, 30, 40, 40)},
        {"image_id": "img", "score": 0.2, "box": (0, 0, 10, 10)},
    ]
    assert average_precision(mixed, ground_truth) == pytest.approx(0.5)
    assert average_precision([], ground_truth) == 0.0
    assert average_precision(true_positive, []) is None
    assert mean_average_precision({"a": 1.0, "b": None}) == 1.0
    assert iou_xyxy((0, 0, 10, 10), (0, 0, 10, 10)) == 1.0


def test_detection_precision_recall_fixture() -> None:
    ground_truth = [{"image_id": "img", "box": (0, 0, 10, 10)}]
    predictions = [
        {"image_id": "img", "score": 0.8, "box": (0, 0, 10, 10)},
        {"image_id": "img", "score": 0.7, "box": (20, 20, 30, 30)},
    ]
    counts = detection_counts_at_threshold(predictions, ground_truth, score_threshold=0.5)
    assert counts["true_positives"] == 1
    assert counts["false_positives"] == 1
    assert counts["false_negatives"] == 0
    assert counts["precision"] == 0.5
    assert counts["recall"] == 1.0


def test_classifiers_forward_without_pretrained_weights() -> None:
    device = get_device(prefer_gpu=False)
    batch = torch.zeros(1, 3, 224, 224, device=device)
    for name in ("mobilenet_v3_large", "resnet18"):
        model = build_classifier(name, num_classes=4, pretrained=False).to(device)
        probabilities = predict_proba(model, batch, device)
        assert tuple(probabilities.shape) == (1, 4)
        assert torch.allclose(probabilities.sum(dim=1), torch.ones(1, device=device), atol=1e-5)
        assert count_parameters(model) > 100_000


def test_resnet_and_mobilenet_are_different_sizes() -> None:
    mobilenet = build_classifier("mobilenet_v3_large", num_classes=3, pretrained=False)
    resnet = build_classifier("resnet18", num_classes=3, pretrained=False)
    assert count_parameters(mobilenet) != count_parameters(resnet)


def test_training_entrypoints_are_blocked() -> None:
    with pytest.raises(RuntimeError):
        train_classifier(enabled=False)
    with pytest.raises(RuntimeError):
        train_detector(enabled=False)
    with pytest.raises(RuntimeError):
        train_hybrid(enabled=False)


def test_yolo_missing_weights_does_not_download(tmp_path: Path) -> None:
    plan = yolo_plan()
    assert plan["download"] == "disabled_in_phase_1"
    assert plan["weights"] is None
    with pytest.raises(FileNotFoundError):
        load_local_yolo(tmp_path / "ausente.pt")


def test_hybrid_crop_and_score() -> None:
    image = np.zeros((100, 120, 3), dtype=np.uint8)
    image[10:30, 15:45] = (255, 0, 0)
    crop = crop_hwc(image, (15, 10, 45, 30), margin=0.0)
    assert crop.shape[0] > 0 and crop.shape[1] > 0
    assert int(crop[0, 0, 0]) == 255
    assert fuse_scores(0.5, 0.25) == 0.125


def test_latency_and_parameter_bytes() -> None:
    calls = {"n": 0}

    def probe() -> None:
        calls["n"] += 1

    report = measure_latency(probe, warmup=1, repeats=3)
    assert calls["n"] == 4
    assert report["repeats"] == 3.0
    layer = nn.Linear(3, 10)
    assert parameter_bytes(layer) == (10 * 3 + 10) * 4
    assert file_size_bytes(Path("arquivo-que-nao-existe.bin")) is None
