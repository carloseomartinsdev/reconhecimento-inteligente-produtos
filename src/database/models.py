"""Modelos persistidos do catálogo comercial e dos preços."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True)
class Product:
    id: str
    name: str
    brand: str
    category: str
    variant: str
    quantity: Decimal
    unit: str
    packaging: str
    barcode: str | None
    reference_image: str | None
    active: bool
    commercial_key: str


@dataclass(frozen=True)
class Establishment:
    id: int
    name: str
    city: str
    state: str
    neighborhood: str | None
    external_id: str | None
    active: bool


@dataclass(frozen=True)
class PriceRecord:
    id: int
    product_id: str
    establishment_id: int
    price: Decimal
    observed_on: date
    recorded_at: datetime
    source_code: str
    price_type: str
    offer_conditions: str
    validation_status: str
    city: str
    state: str
