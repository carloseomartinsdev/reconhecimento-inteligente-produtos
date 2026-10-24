"""Conversão para preço por quilograma, litro ou unidade."""

from __future__ import annotations

from decimal import Decimal

from catalog.identity import canonical_unit


def base_quantity(quantity: Decimal, unit: str) -> tuple[Decimal, str]:
    canonical = canonical_unit(unit)
    if canonical == "g":
        return quantity / Decimal(1000), "kg"
    if canonical == "kg":
        return quantity, "kg"
    if canonical == "ml":
        return quantity / Decimal(1000), "L"
    if canonical == "L":
        return quantity, "L"
    return quantity, "un"


def package_to_unit_price(package_price: Decimal, quantity: Decimal, unit: str) -> tuple[Decimal, str]:
    converted, base_unit = base_quantity(quantity, unit)
    return package_price / converted, base_unit
