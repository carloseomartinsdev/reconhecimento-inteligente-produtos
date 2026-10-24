"""Identidade comercial.

A identidade é a combinação de marca, variante, quantidade e unidade.
Embalagens com quantidades diferentes permanecem produtos diferentes.
350 ml e 1 L não são unificados, ainda que a unidade de base seja a mesma.
"""

from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation

UNITS = ("g", "kg", "ml", "L", "un")
_UNIT_ALIASES = {
    "g": "g",
    "gr": "g",
    "grama": "g",
    "gramas": "g",
    "kg": "kg",
    "quilo": "kg",
    "quilos": "kg",
    "ml": "ml",
    "l": "L",
    "lt": "L",
    "litro": "L",
    "litros": "L",
    "un": "un",
    "und": "un",
    "unidade": "un",
    "unidades": "un",
}
_BARCODE = re.compile(r"^\d{8}$|^\d{12,14}$")


class IdentityError(ValueError):
    """Dados comerciais que não formam uma identidade utilizável."""


def fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    without_marks = "".join(character for character in normalized if not unicodedata.combining(character))
    return " ".join(without_marks.split())


def canonical_unit(unit: str) -> str:
    key = fold(unit)
    if key not in _UNIT_ALIASES:
        raise IdentityError(f"Unidade não prevista: {unit}. Use {', '.join(UNITS)}.")
    return _UNIT_ALIASES[key]


def parse_quantity(quantity: Decimal | int | str) -> Decimal:
    try:
        value = quantity if isinstance(quantity, Decimal) else Decimal(str(quantity).replace(",", "."))
    except (InvalidOperation, ValueError) as exc:
        raise IdentityError(f"Quantidade inválida: {quantity}.") from exc
    if value <= 0:
        raise IdentityError("A quantidade da embalagem precisa ser positiva.")
    return value


def quantity_text(quantity: Decimal) -> str:
    rendered = format(quantity.quantize(Decimal("0.001")), "f")
    return rendered.rstrip("0").rstrip(".")


def commercial_key(
    brand: str,
    variant: str,
    quantity: Decimal | int | str,
    unit: str,
    name: str = "",
    packaging: str = "",
) -> str:
    """Chave da fase 2.1, com nome e embalagem quando a embalagem foi informada.

    O acréscimo não altera cadastros antigos, que continuam com quatro campos.
    """
    parsed = parse_quantity(quantity)
    parts = [fold(brand), fold(variant), quantity_text(parsed), canonical_unit(unit)]
    if packaging.strip():
        parts.extend((fold(name), fold(packaging)))
    return "|".join(parts)


def normalize_barcode(barcode: str | None) -> str | None:
    if barcode is None:
        return None
    digits = barcode.strip()
    if digits == "":
        return None
    if not _BARCODE.fullmatch(digits):
        raise IdentityError("O código de barras informado não tem o formato GTIN/EAN de 8, 12, 13 ou 14 dígitos.")
    return digits
