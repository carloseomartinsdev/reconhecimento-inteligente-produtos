"""OCR de etiqueta.

O valor encontrado não é tratado como o preço do produto.
A confirmação manual permanece obrigatória.
Quando o mecanismo não informa confiança, o campo fica nulo.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import cv2

from ocr.parse import find_money_candidates
from ocr.preprocess import preprocess_label
from preprocessing.validate import validate_image


def tesseract_executable() -> str | None:
    return shutil.which("tesseract")


def read_label(path: Path) -> dict[str, object]:
    issues = validate_image(Path(path))
    errors = [issue for issue in issues if issue["level"] == "error"]
    if errors:
        return {
            "candidatos": [],
            "requer_confirmacao": True,
            "mecanismo": "imagem_invalida",
            "erros": errors,
        }
    if tesseract_executable() is None:
        return {
            "candidatos": [],
            "requer_confirmacao": True,
            "mecanismo": "indisponivel",
            "mensagem": "O executável tesseract não está instalado. O texto da etiqueta pode ser digitado.",
        }
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        return {
            "candidatos": [],
            "requer_confirmacao": True,
            "mecanismo": "imagem_invalida",
            "erros": [{"level": "error", "code": "opencv_decode", "message": "OpenCV não decodificou o arquivo."}],
        }
    processed = preprocess_label(image)
    text = _recognize(processed)
    return {
        "candidatos": find_money_candidates(text),
        "requer_confirmacao": True,
        "mecanismo": "tesseract",
        "texto": text,
    }


def _recognize(image) -> str:
    import pytesseract

    executable = tesseract_executable()
    if executable is not None:
        pytesseract.pytesseract.tesseract_cmd = executable
    try:
        return str(pytesseract.image_to_string(image, lang="por"))
    except pytesseract.TesseractError:
        return str(pytesseract.image_to_string(image))
