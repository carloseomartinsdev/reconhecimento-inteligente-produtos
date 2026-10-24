"""Modelo D.

O detector propõe caixas. A CNN classifica cada recorte. A caixa permanece;
o rótulo e a confiança combinada vêm da segunda etapa. Nenhum dos dois
modelos é treinado aqui.
"""

from __future__ import annotations

import numpy as np


def clip_box_xyxy(
    box: tuple[float, float, float, float],
    width: int,
    height: int,
) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = box
    x1 = min(max(x1, 0.0), float(width))
    x2 = min(max(x2, 0.0), float(width))
    y1 = min(max(y1, 0.0), float(height))
    y2 = min(max(y2, 0.0), float(height))
    return x1, y1, x2, y2


def expand_box_xyxy(
    box: tuple[float, float, float, float],
    margin: float,
    width: int,
    height: int,
) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = box
    box_width = x2 - x1
    box_height = y2 - y1
    expanded = (
        x1 - box_width * margin,
        y1 - box_height * margin,
        x2 + box_width * margin,
        y2 + box_height * margin,
    )
    return clip_box_xyxy(expanded, width, height)


def crop_hwc(
    image: np.ndarray,
    box: tuple[float, float, float, float],
    margin: float = 0.0,
) -> np.ndarray:
    if image.ndim != 3:
        raise ValueError("crop_hwc espera uma imagem HWC.")
    height, width = image.shape[:2]
    x1, y1, x2, y2 = expand_box_xyxy(box, margin, width, height)
    left = int(np.floor(x1))
    top = int(np.floor(y1))
    right = int(np.ceil(x2))
    bottom = int(np.ceil(y2))
    right = max(right, left + 1)
    bottom = max(bottom, top + 1)
    right = min(right, width)
    bottom = min(bottom, height)
    crop = image[top:bottom, left:right]
    if crop.size == 0:
        raise ValueError("Recorte vazio.")
    return crop


def fuse_scores(detector_confidence: float, class_probability: float) -> float:
    if not 0.0 <= detector_confidence <= 1.0:
        raise ValueError("detector_confidence fora de [0, 1].")
    if not 0.0 <= class_probability <= 1.0:
        raise ValueError("class_probability fora de [0, 1].")
    return float(detector_confidence * class_probability)


def train_hybrid(*args: object, enabled: bool = False, **kwargs: object) -> None:
    del args, kwargs
    if not enabled:
        raise RuntimeError("Treinamento híbrido desabilitado na fase 1.")
    raise NotImplementedError("O treino híbrido será implementado na fase experimental.")
