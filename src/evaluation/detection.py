"""Precisão média para detecção em caixas xyxy.

A implementação usa a área sob a curva precision-recall com envelope de
precisão. Ela serve para auditoria e testes. O mAP reportado na fase
experimental do YOLO deve sair do validador do Ultralytics, que segue o
protocolo 101-point usado pela comunidade COCO. Os dois números não são
intercambiáveis sem essa ressalva.
"""

from __future__ import annotations


def iou_xyxy(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> float:
    x1 = max(first[0], second[0])
    y1 = max(first[1], second[1])
    x2 = min(first[2], second[2])
    y2 = min(first[3], second[3])
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    if intersection == 0.0:
        return 0.0
    area_first = max(0.0, first[2] - first[0]) * max(0.0, first[3] - first[1])
    area_second = max(0.0, second[2] - second[0]) * max(0.0, second[3] - second[1])
    union = area_first + area_second - intersection
    if union <= 0.0:
        return 0.0
    return intersection / union


def average_precision(
    predictions: list[dict[str, object]],
    ground_truth: list[dict[str, object]],
    iou_threshold: float = 0.5,
) -> float | None:
    if len(ground_truth) == 0:
        return None
    gt_by_image: dict[object, list[dict[str, object]]] = {}
    for item in ground_truth:
        gt_by_image.setdefault(item["image_id"], []).append(
            {"box": item["box"], "matched": False}
        )
    ordered = sorted(predictions, key=lambda item: float(item["score"]), reverse=True)
    if not ordered:
        return 0.0

    steps: list[tuple[int, int]] = []
    for prediction in ordered:
        candidates = gt_by_image.get(prediction["image_id"], [])
        best_iou = 0.0
        best = None
        for candidate in candidates:
            if candidate["matched"]:
                continue
            value = iou_xyxy(prediction["box"], candidate["box"])  # type: ignore[arg-type]
            if value > best_iou:
                best_iou = value
                best = candidate
        if best is not None and best_iou >= iou_threshold:
            best["matched"] = True
            steps.append((1, 0))
        else:
            steps.append((0, 1))

    recalls = [0.0]
    precisions = [1.0]
    cum_tp = 0
    cum_fp = 0
    n_gt = len(ground_truth)
    for true_positive, false_positive in steps:
        cum_tp += true_positive
        cum_fp += false_positive
        recalls.append(cum_tp / n_gt)
        precisions.append(cum_tp / (cum_tp + cum_fp))
    for index in range(len(precisions) - 2, -1, -1):
        precisions[index] = max(precisions[index], precisions[index + 1])
    area = 0.0
    for index in range(1, len(recalls)):
        area += (recalls[index] - recalls[index - 1]) * precisions[index]
    return area


def mean_average_precision(per_class: dict[str, float | None]) -> float | None:
    values = [value for value in per_class.values() if value is not None]
    if not values:
        return None
    return sum(values) / len(values)


def detection_counts_at_threshold(
    predictions: list[dict[str, object]],
    ground_truth: list[dict[str, object]],
    iou_threshold: float = 0.5,
    score_threshold: float = 0.5,
) -> dict[str, float | None]:
    kept = [item for item in predictions if float(item["score"]) >= score_threshold]
    matched_gt = 0
    gt_by_image: dict[object, list[dict[str, object]]] = {}
    for item in ground_truth:
        gt_by_image.setdefault(item["image_id"], []).append(
            {"box": item["box"], "matched": False}
        )
    false_positives = 0
    for prediction in sorted(kept, key=lambda item: float(item["score"]), reverse=True):
        candidates = gt_by_image.get(prediction["image_id"], [])
        best_iou = 0.0
        best = None
        for candidate in candidates:
            if candidate["matched"]:
                continue
            value = iou_xyxy(prediction["box"], candidate["box"])  # type: ignore[arg-type]
            if value > best_iou:
                best_iou = value
                best = candidate
        if best is not None and best_iou >= iou_threshold:
            best["matched"] = True
            matched_gt += 1
        else:
            false_positives += 1
    false_negatives = len(ground_truth) - matched_gt
    precision = None if matched_gt + false_positives == 0 else matched_gt / (matched_gt + false_positives)
    recall = None if len(ground_truth) == 0 else matched_gt / len(ground_truth)
    return {
        "true_positives": matched_gt,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
    }
