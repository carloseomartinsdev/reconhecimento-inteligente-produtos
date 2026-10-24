"""Limites e critérios de confiabilidade, lidos da configuração."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class PricePolicy:
    excellent_below: Decimal
    good_below: Decimal
    within_until: Decimal
    above_until: Decimal
    min_records: int
    max_age_days: int
    min_establishments: int
    regular_only: bool

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> PricePolicy:
        pricing = payload["pricing"]
        bands = pricing["bands"]
        reliability = pricing["reliability"]
        return cls(
            excellent_below=Decimal(str(bands["excellent_below"])),
            good_below=Decimal(str(bands["good_below"])),
            within_until=Decimal(str(bands["within_until"])),
            above_until=Decimal(str(bands["above_until"])),
            min_records=int(reliability["min_records"]),
            max_age_days=int(reliability["max_age_days"]),
            min_establishments=int(reliability["min_establishments"]),
            regular_only=bool(reliability["regular_only"]),
        )


def classify_percent(percent: Decimal, policy: PricePolicy) -> str:
    if percent < policy.excellent_below:
        return "Excelente preço"
    if percent < policy.good_below:
        return "Bom preço"
    if percent <= policy.within_until:
        return "Dentro da média"
    if percent <= policy.above_until:
        return "Acima da média"
    return "Muito acima da média"
