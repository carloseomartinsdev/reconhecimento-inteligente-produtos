"""Indicadores descritivos calculados com Decimal."""

from __future__ import annotations

from decimal import Decimal


def mean(values: list[Decimal]) -> Decimal | None:
    if not values:
        return None
    return sum(values, Decimal("0")) / Decimal(len(values))


def median(values: list[Decimal]) -> Decimal | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / Decimal(2)


def population_std(values: list[Decimal]) -> Decimal | None:
    if len(values) < 2:
        return None
    center = mean(values)
    assert center is not None
    variance = sum((value - center) ** 2 for value in values) / Decimal(len(values))
    return variance.sqrt()


def quartile(values: list[Decimal], probability: Decimal) -> Decimal | None:
    """Interpolação linear na posição (n - 1) * p."""
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = Decimal(len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - Decimal(lower)
    return ordered[lower] * (Decimal(1) - weight) + ordered[upper] * weight


def percent_difference(value: Decimal, reference: Decimal) -> Decimal | None:
    if reference == 0:
        return None
    return (value - reference) / reference * Decimal(100)


def summarize(values: list[Decimal]) -> dict[str, Decimal | int | None]:
    return {
        "count": len(values),
        "minimum": min(values) if values else None,
        "maximum": max(values) if values else None,
        "mean": mean(values),
        "median": median(values),
        "population_std": population_std(values),
        "q1": quartile(values, Decimal("0.25")),
        "q3": quartile(values, Decimal("0.75")),
    }
