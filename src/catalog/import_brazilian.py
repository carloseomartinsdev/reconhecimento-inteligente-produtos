"""Copia o catálogo verificado para o SQLite, sem criar preço."""

from __future__ import annotations

import json
from pathlib import Path

from database.store import Store, StoreError


def import_products(store: Store, path: Path) -> int:
    if not path.exists():
        return 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    inserted = 0
    for product in payload.get("produtos", []):
        if product.get("status_comercial") != "validado":
            continue
        barcode = product.get("codigo_barras")
        if barcode and store.find_by_barcode(str(barcode)) is not None:
            continue
        try:
            store.register_product(
                name=product["nome"],
                brand=product["marca"],
                category=product["categoria"],
                variant=product.get("variante") or "",
                quantity=product["quantidade"],
                unit=product["unidade"],
                packaging=product.get("tipo_embalagem") or "",
                barcode=barcode,
                product_id=product["id"],
                active=bool(product.get("ativo", True)),
            )
        except StoreError:
            continue
        inserted += 1
    return inserted
