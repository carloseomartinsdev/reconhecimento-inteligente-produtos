"""Testes do leitor de etiquetas.

Os textos são sintéticos. Um número reconhecido não vira, sozinho, o preço do produto.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from ocr.parse import find_money_candidates
from ocr.preprocess import preprocess_label
from ocr.reader import read_label, tesseract_executable


def test_money_candidates_keep_original_text_and_null_confidence() -> None:
    candidates = find_money_candidates("Etiqueta sintética R$ 5,49 e também 6,00. Volume 350 ml.")
    assert candidates[0]["valor"] == "5.49"
    assert candidates[0]["texto_original"] == "R$ 5,49"
    assert candidates[0]["confianca"] is None
    assert {item["valor"] for item in candidates} == {"5.49", "6.00"}
    assert find_money_candidates("350 ml") == []
    assert find_money_candidates("") == []


def test_preprocess_returns_binary_image() -> None:
    image = np.full((40, 90, 3), 255, dtype=np.uint8)
    image[10:30, 10:70] = (0, 0, 0)
    processed = preprocess_label(image)
    assert processed.ndim == 2
    assert processed.dtype == np.uint8
    assert processed.shape[0] >= 40


def test_reader_does_not_invent_a_price_without_an_ocr_engine(tmp_path: Path) -> None:
    path = tmp_path / "etiqueta_sintetica.png"
    Image.new("RGB", (80, 40), color=(255, 255, 255)).save(path)
    result = read_label(path)
    assert result["requer_confirmacao"] is True
    if tesseract_executable() is None:
        assert result["mecanismo"] == "indisponivel"
        assert result["candidatos"] == []


def test_invalid_image_has_no_candidates(tmp_path: Path) -> None:
    missing = tmp_path / "ausente.jpg"
    result = read_label(missing)
    assert result["candidatos"] == []
    assert result["mecanismo"] == "imagem_invalida"


def test_manual_flow_confirms_ocr_text_before_comparison(tmp_path: Path) -> None:
    from datetime import date

    from database.store import Store
    from pricing.engine import CLASSIFIED, PriceEngine
    from pricing.policy import PricePolicy
    from decimal import Decimal

    candidates = find_money_candidates("R$ 5,49")
    assert len(candidates) == 1
    confirmed = candidates[0]["valor"]
    with Store(tmp_path / "sintetico.sqlite") as store:
        product = store.register_product(
            name="Item sintético", brand="Marca Sintética", category="Teste", quantity=1, unit="un"
        )
        places = [
            store.register_establishment(name=f"Loja sintética {index}", city="Campinas", state="SP")
            for index in range(2)
        ]
        for price, place in (("5.00", places[0]), ("5.50", places[1]), ("6.00", places[0])):
            store.register_price(
                product_id=product.id,
                establishment_id=place.id,
                price=price,
                observed_on=date.today(),
                source_code="label_photo",
                price_type="regular",
            )
        report = PriceEngine(
            store,
            PricePolicy(
                excellent_below=Decimal("-10"),
                good_below=Decimal("-3"),
                within_until=Decimal("5"),
                above_until=Decimal("15"),
                min_records=3,
                max_age_days=30,
                min_establishments=2,
                regular_only=True,
            ),
        ).compare(product_id=product.id, informed_price=str(confirmed), state="SP", city="Campinas")
        assert report.status == CLASSIFIED
        assert report.package_price == Decimal("5.49")
        assert report.classification is not None
