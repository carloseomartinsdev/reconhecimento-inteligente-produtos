"""Operações clássicas de pré-processamento usadas no experimento E2.

Cada função devolve uma imagem e não produz métrica de reconhecimento.
A comparação entre presets fica para a fase de treino.
"""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image


def resize_stretch(image: np.ndarray, size: int) -> np.ndarray:
    """Redimensiona para um quadrado, alterando a proporção."""
    return cv2.resize(image, (size, size), interpolation=cv2.INTER_LINEAR)


def letterbox(image: np.ndarray, size: int, pad_value: int = 114) -> np.ndarray:
    """Redimensiona preservando a proporção e completa com borda constante."""
    height, width = image.shape[:2]
    scale = size / max(height, width)
    new_width = max(1, int(round(width * scale)))
    new_height = max(1, int(round(height * scale)))
    resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
    channels = 1 if resized.ndim == 2 else resized.shape[2]
    if channels == 1:
        canvas = np.full((size, size), pad_value, dtype=resized.dtype)
    else:
        canvas = np.full((size, size, channels), pad_value, dtype=resized.dtype)
    top = (size - new_height) // 2
    left = (size - new_width) // 2
    canvas[top : top + new_height, left : left + new_width] = resized
    return canvas


def equalize_rgb(image: np.ndarray) -> np.ndarray:
    """Equaliza o canal de luminância de uma imagem RGB uint8."""
    if image.dtype != np.uint8:
        raise ValueError("equalize_rgb espera uint8.")
    ycrcb = cv2.cvtColor(image, cv2.COLOR_RGB2YCrCb)
    ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
    return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2RGB)


def apply_clahe(image: np.ndarray, clip_limit: float = 2.0, tile_size: int = 8) -> np.ndarray:
    """Aplica CLAHE na luminância e devolve RGB uint8."""
    if image.dtype != np.uint8:
        raise ValueError("apply_clahe espera uint8.")
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)


def apply_preset(image: np.ndarray, preset: str, size: int = 224) -> np.ndarray:
    if preset == "identity_scale":
        return resize_stretch(image, size)
    if preset == "letterbox":
        return letterbox(image, size)
    if preset == "baseline_imagenet":
        return resize_stretch(image, size)
    if preset == "equalize":
        return resize_stretch(equalize_rgb(image), size)
    if preset == "clahe":
        return resize_stretch(apply_clahe(image), size)
    raise ValueError(f"Preset desconhecido: {preset}")


def pil_from_array(image: np.ndarray) -> Image.Image:
    return Image.fromarray(image)
