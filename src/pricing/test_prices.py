"""Preços sintéticos para a demonstração local.

Os valores não são coleta de mercado. A condição da oferta deixa isso explícito.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from catalog.service import Catalog
from database.store import Store

TEST_OFFER = "Preço de teste. Não é coleta de mercado."
SHOPS = (
    ("teste-centro", "Mercado Teste Centro", "Campinas", "SP", "Centro"),
    ("teste-norte", "Mercado Teste Norte", "Campinas", "SP", "Norte"),
    ("teste-sul", "Mercado Teste Sul", "Campinas", "SP", "Sul"),
    ("teste-oeste", "Mercado Teste Oeste", "Campinas", "SP", "Oeste"),
    ("teste-atacado", "Atacado Teste", "São Paulo", "SP", "Barra Funda"),
)
FACTORS = (
    Decimal("0.94"),
    Decimal("0.98"),
    Decimal("1.00"),
    Decimal("1.05"),
    Decimal("1.11"),
)
PER_UNIT = {
    "Arroz": Decimal("5.80"),
    "Feijão": Decimal("8.40"),
    "Açúcar": Decimal("4.20"),
    "Café": Decimal("36.00"),
    "Leite UHT": Decimal("5.10"),
    "Leite em pó": Decimal("28.00"),
    "Óleo de soja": Decimal("7.80"),
    "Farinhas e flocão": Decimal("4.60"),
    "Macarrão": Decimal("8.20"),
    "Sal": Decimal("2.40"),
    "Manteiga": Decimal("42.00"),
}


def ensure_test_prices(store: Store, *, today: date | None = None) -> int:
    """Grava cinco preços regulares por produto que ainda não tem preço de teste."""
    reference = today or date.today()
    shops = _ensure_shops(store)
    inserted = 0
    for product in Catalog(store).list_active():
        if _already_seeded(store, product.id):
            continue
        base = _pack_price(product.category, product.quantity, product.unit)
        for offset, (shop_id, factor) in enumerate(zip(shops, FACTORS, strict=True)):
            amount = (base * factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            store.register_price(
                product_id=product.id,
                establishment_id=shop_id,
                price=f"{amount:.2f}",
                observed_on=reference - timedelta(days=offset * 2),
                source_code="manual",
                price_type="regular",
                offer_conditions=TEST_OFFER,
                validation_status="valid",
                as_of=reference,
            )
            inserted += 1
    return inserted


def _ensure_shops(store: Store) -> list[int]:
    existing = {
        place.external_id: place.id
        for place in store.list_establishments(active_only=False)
        if place.external_id
    }
    identifiers: list[int] = []
    for external_id, name, city, state, neighborhood in SHOPS:
        found = existing.get(external_id)
        if found is None:
            created = store.register_establishment(
                name=name,
                city=city,
                state=state,
                neighborhood=neighborhood,
                external_id=external_id,
            )
            found = created.id
        identifiers.append(found)
    return identifiers


def _already_seeded(store: Store, product_id: str) -> bool:
    return any(record.offer_conditions == TEST_OFFER for record in store.list_prices(product_id))


def _pack_price(category: str, quantity: Decimal, unit: str) -> Decimal:
    per_unit = PER_UNIT.get(category, Decimal("8.00"))
    if unit in {"kg", "L"}:
        amount = quantity * per_unit
    elif unit in {"g", "ml"}:
        amount = quantity / Decimal("1000") * per_unit
    else:
        amount = per_unit
    if amount < Decimal("1.00"):
        return Decimal("1.00")
    return amount
