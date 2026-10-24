"""Validação de anotações COCO e de rótulos YOLO normalizados."""

from __future__ import annotations

import json
from pathlib import Path


def load_json(path: Path) -> dict:
    with Path(path).open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("A anotação JSON precisa ser um objeto.")
    return payload


def categories_from_coco(payload: dict) -> list[dict[str, object]]:
    rows = []
    raw_names = payload.get("__raw_Chinese_name_df") or payload.get("raw_Chinese_name_df") or []
    by_id: dict[int, dict] = {}
    if isinstance(raw_names, list):
        for item in raw_names:
            if isinstance(item, dict) and "category_id" in item:
                by_id[int(item["category_id"])] = item
    for category in payload.get("categories", []):
        category_id = int(category["id"])
        extra = by_id.get(category_id, {})
        rows.append(
            {
                "category_id": category_id,
                "name": str(category.get("name", "")),
                "supercategory": str(category.get("supercategory", "")),
                "chinese_name": str(extra.get("name", "")),
                "sku_name": str(extra.get("sku_name", "")),
            }
        )
    return rows


def validate_coco(payload: dict, image_root: Path | None = None) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for key in ("images", "annotations", "categories"):
        if key not in payload:
            issues.append(_issue("error", "missing_key", f"Campo ausente: {key}"))
    if issues:
        return issues

    category_ids = set()
    for category in payload["categories"]:
        if "id" not in category or "name" not in category:
            issues.append(_issue("error", "category_fields", "Categoria sem id ou name."))
            continue
        category_id = int(category["id"])
        if category_id in category_ids:
            issues.append(_issue("error", "duplicate_category", f"category_id repetido: {category_id}"))
        category_ids.add(category_id)

    images: dict[int, dict] = {}
    for image in payload["images"]:
        if "id" not in image or "file_name" not in image:
            issues.append(_issue("error", "image_fields", "Imagem sem id ou file_name."))
            continue
        image_id = int(image["id"])
        if image_id in images:
            issues.append(_issue("error", "duplicate_image", f"image_id repetido: {image_id}"))
        images[image_id] = image
        if image_root is not None:
            file_path = image_root / str(image["file_name"])
            if not file_path.is_file():
                issues.append(
                    _issue("error", "missing_image", f"Imagem anotada não encontrada: {image['file_name']}")
                )

    seen_annotations = set()
    for annotation in payload["annotations"]:
        required = ("id", "image_id", "category_id", "bbox")
        if any(field not in annotation for field in required):
            issues.append(_issue("error", "annotation_fields", "Anotação sem id, image_id, category_id ou bbox."))
            continue
        annotation_id = int(annotation["id"])
        if annotation_id in seen_annotations:
            issues.append(_issue("error", "duplicate_annotation", f"annotation id repetido: {annotation_id}"))
        seen_annotations.add(annotation_id)
        image_id = int(annotation["image_id"])
        category_id = int(annotation["category_id"])
        if image_id not in images:
            issues.append(_issue("error", "unknown_image", f"image_id {image_id} não existe em images."))
        if category_id not in category_ids:
            issues.append(_issue("error", "unknown_category", f"category_id {category_id} não existe em categories."))
        bbox_issue = _validate_bbox(annotation.get("bbox"), images.get(image_id))
        if bbox_issue is not None:
            issues.append(bbox_issue)
        if "point_xy" in annotation and image_id in images:
            point_issue = _validate_point(annotation["point_xy"], images[image_id])
            if point_issue is not None:
                issues.append(point_issue)
    return issues


def validate_yolo_label_text(text: str, num_classes: int | None = None) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 5:
            issues.append(_issue("error", "yolo_fields", f"Linha {line_number} não tem 5 campos."))
            continue
        try:
            class_id = int(parts[0])
            cx, cy, width, height = (float(part) for part in parts[1:])
        except ValueError:
            issues.append(_issue("error", "yolo_parse", f"Linha {line_number} não é numérica."))
            continue
        if num_classes is not None and not 0 <= class_id < num_classes:
            issues.append(_issue("error", "yolo_class", f"Classe {class_id} fora do intervalo na linha {line_number}."))
        for name, value in (("cx", cx), ("cy", cy), ("w", width), ("h", height)):
            if not 0.0 <= value <= 1.0:
                issues.append(
                    _issue("error", "yolo_range", f"{name}={value} fora de [0, 1] na linha {line_number}.")
                )
        if width <= 0 or height <= 0:
            issues.append(_issue("error", "yolo_size", f"Largura ou altura nula na linha {line_number}."))
    return issues


def _validate_bbox(bbox: object, image: dict | None) -> dict[str, str] | None:
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        return _issue("error", "bbox_shape", "bbox precisa ter quatro números [x, y, w, h].")
    try:
        x, y, width, height = (float(value) for value in bbox)
    except (TypeError, ValueError):
        return _issue("error", "bbox_type", "bbox contém valor não numérico.")
    if width <= 0 or height <= 0:
        return _issue("error", "bbox_size", "bbox com largura ou altura não positiva.")
    if image is None or "width" not in image or "height" not in image:
        return None
    image_width = float(image["width"])
    image_height = float(image["height"])
    tolerance = 1.0
    if x < -tolerance or y < -tolerance or x + width > image_width + tolerance or y + height > image_height + tolerance:
        return _issue("error", "bbox_bounds", "bbox ultrapassa os limites da imagem.")
    return None


def _validate_point(point: object, image: dict) -> dict[str, str] | None:
    if not isinstance(point, (list, tuple)) or len(point) != 2:
        return _issue("error", "point_shape", "point_xy precisa ter dois números.")
    try:
        x, y = float(point[0]), float(point[1])
    except (TypeError, ValueError):
        return _issue("error", "point_type", "point_xy contém valor não numérico.")
    if "width" not in image or "height" not in image:
        return None
    if not (0 <= x <= float(image["width"]) and 0 <= y <= float(image["height"])):
        return _issue("warning", "point_bounds", "point_xy cai fora da imagem.")
    return None


def _issue(level: str, code: str, message: str) -> dict[str, str]:
    return {"level": level, "code": code, "message": message}
