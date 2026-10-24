"""Pré-processamento de etiqueta antes do OCR.

As escolhas abaixo são um ponto de partida para o experimento E7.
Elas não foram avaliadas em etiquetas reais.
"""

from __future__ import annotations

import cv2
import numpy as np


def preprocess_label(image_bgr: np.ndarray) -> np.ndarray:
    if image_bgr.ndim != 3:
        raise ValueError("A imagem da etiqueta precisa ter três canais.")
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape[:2]
    if min(height, width) < 80:
        gray = cv2.resize(gray, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
    smoothed = cv2.GaussianBlur(gray, (3, 3), 0)
    return cv2.adaptiveThreshold(
        smoothed,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        5,
    )
