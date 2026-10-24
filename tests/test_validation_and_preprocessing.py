from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from evaluation.annotations import validate_coco, validate_yolo_label_text
from preprocessing.ops import apply_clahe, apply_preset, letterbox
from preprocessing.transforms import build_eval_transform
from preprocessing.validate import validate_image


def test_valid_image_and_rejected_empty_file(tmp_path: Path) -> None:
    image_path = tmp_path / "sample.png"
    Image.new("RGB", (64, 48), color=(20, 40, 60)).save(image_path)
    assert validate_image(image_path) == []

    empty = tmp_path / "empty.jpg"
    empty.write_bytes(b"")
    codes = {issue["code"] for issue in validate_image(empty)}
    assert "empty_file" in codes

    missing = validate_image(tmp_path / "ausente.jpg")
    assert missing[0]["code"] == "missing_file"


def test_small_image_is_warning(tmp_path: Path) -> None:
    image_path = tmp_path / "tiny.png"
    Image.new("RGB", (8, 8), color=(0, 0, 0)).save(image_path)
    issues = validate_image(image_path, min_side=32)
    assert any(issue["code"] == "small" and issue["level"] == "warning" for issue in issues)


def test_letterbox_preserves_canvas_and_clahe_keeps_shape() -> None:
    image = np.zeros((40, 80, 3), dtype=np.uint8)
    image[:, :, 0] = 30
    boxed = letterbox(image, 64)
    assert boxed.shape == (64, 64, 3)
    assert boxed[0, 0, 0] == 114
    enhanced = apply_clahe(image)
    assert enhanced.shape == image.shape
    assert enhanced.dtype == np.uint8
    for preset in ("baseline_imagenet", "letterbox", "clahe", "equalize", "identity_scale"):
        output = apply_preset(image, preset, size=32)
        assert output.shape[:2] == (32, 32)


def test_eval_transform_output_shape() -> None:
    image = Image.new("RGB", (90, 50), color=(10, 20, 30))
    tensor = build_eval_transform(image_size=224)(image)
    assert tuple(tensor.shape) == (3, 224, 224)


def test_coco_accepts_consistent_annotation_and_rejects_bad_box() -> None:
    payload = {
        "images": [{"id": 1, "file_name": "a.jpg", "width": 100, "height": 80}],
        "categories": [{"id": 7, "name": "7_drink", "supercategory": "drink"}],
        "annotations": [
            {
                "id": 3,
                "image_id": 1,
                "category_id": 7,
                "bbox": [10, 10, 20, 15],
                "point_xy": [20, 18],
            }
        ],
    }
    assert validate_coco(payload) == []
    payload["annotations"][0]["bbox"] = [90, 10, 30, 10]
    codes = {issue["code"] for issue in validate_coco(payload)}
    assert "bbox_bounds" in codes


def test_coco_unknown_category_and_yolo_label(tmp_path: Path) -> None:
    payload = {
        "images": [{"id": 1, "file_name": "a.jpg", "width": 50, "height": 50}],
        "categories": [{"id": 1, "name": "item"}],
        "annotations": [{"id": 1, "image_id": 1, "category_id": 9, "bbox": [1, 1, 2, 2]}],
    }
    assert any(issue["code"] == "unknown_category" for issue in validate_coco(payload))
    text = "0 0.5 0.5 0.2 0.2\n1 1.2 0.5 0.1 0.1\n"
    issues = validate_yolo_label_text(text, num_classes=2)
    assert any(issue["code"] == "yolo_range" for issue in issues)
    assert validate_yolo_label_text("0 0.5 0.5 0.25 0.25\n", num_classes=1) == []
    path = tmp_path / "sample.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert path.is_file()


def test_unknown_preset_raises() -> None:
    image = np.zeros((8, 8, 3), dtype=np.uint8)
    with pytest.raises(ValueError):
        apply_preset(image, "inexistente")
