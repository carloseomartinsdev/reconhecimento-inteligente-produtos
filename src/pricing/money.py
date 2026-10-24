"""Valores monetários em Decimal.

Nenhuma operação deste módulo converte o preço para float.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN

CENT = Decimal("0.01")


class MoneyError(ValueError):
    """Valor que não pode ser usado como preço."""


def parse_price(value: Decimal | int | str) -> Decimal:
    if isinstance(value, float):
        raise MoneyError("Preço em float não é aceito. Informe o valor como texto ou Decimal.")
    if isinstance(value, Decimal):
        parsed = value
    else:
        text = str(value).strip().replace("R$", "").strip()
        if text == "":
            raise MoneyError("Preço vazio.")
        if text.startswith("-"):
            raise MoneyError("Preço negativo não é aceito.")
        if "," in text and "." in text:
            text = text.replace(".", "").replace(",", ".")
        elif "," in text:
            text = text.replace(",", ".")
        try:
            parsed = Decimal(text)
        except InvalidOperation as exc:
            raise MoneyError(f"Preço inválido: {value}.") from exc
    if parsed <= 0:
        raise MoneyError("Preço precisa ser maior que zero.")
    quantized = parsed.quantize(CENT, rounding=ROUND_HALF_EVEN)
    if quantized != parsed:
        raise MoneyError("Preço com mais de duas casas decimais não é aceito.")
    return quantized


def format_price(value: Decimal) -> str:
    quantized = value.quantize(CENT, rounding=ROUND_HALF_EVEN)
    return f"{quantized:.2f}"
