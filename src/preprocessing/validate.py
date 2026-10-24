"""Validação de arquivos de imagem sem depender do dataset completo."""

from __future__ import annotations

from pathlib import Path

import cv2
from PIL import Image, UnidentifiedImageError

ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
ACCEPTED_MODES = {"RGB", "L", "RGBA"}


def validate_image(path: Path, min_side: int = 32) -> list[dict[str, str]]:
    path = Path(path)
    issues: list[dict[str, str]] = []
    if not path.is_file():
        return [_issue("error", "missing_file", f"Arquivo ausente: {path}")]
    if path.suffix.lower() not in ALLOWED_SUFFIXES:
        issues.append(_issue("error", "extension", f"Extensão não prevista: {path.suffix}"))
    if path.stat().st_size == 0:
        return issues + [_issue("error", "empty_file", "Arquivo com zero bytes.")]

    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            image.load()
            width, height = image.size
            mode = image.mode
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        return issues + [_issue("error", "unreadable", f"Pillow não leu a imagem: {exc}")]

    if mode not in ACCEPTED_MODES:
        issues.append(_issue("warning", "mode", f"Modo de cor {mode} será convertido antes do treino."))
    if min(width, height) < min_side:
        issues.append(
            _issue("warning", "small", f"Lado mínimo {min(width, height)} px é menor que {min_side} px.")
        )
    if width < 1 or height < 1:
        issues.append(_issue("error", "dimensions", "Dimensões inválidas."))

    decoded = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if decoded is None:
        issues.append(_issue("error", "opencv_decode", "OpenCV não decodificou o arquivo."))
    return issues


def _issue(level: str, code: str, message: str) -> dict[str, str]:
    return {"level": level, "code": code, "message": message}
