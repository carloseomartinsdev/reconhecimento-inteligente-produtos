"""Fachada do catálogo comercial sobre o banco local."""

from __future__ import annotations

from decimal import Decimal

from database.models import Product
from database.store import Store


class Catalog:
    def __init__(self, store: Store):
        self.store = store

    def register(self, **fields: object) -> Product:
        return self.store.register_product(**fields)  # type: ignore[arg-type]

    def update(self, product_id: str, **fields: object) -> Product:
        return self.store.update_product(product_id, **fields)

    def get(self, product_id: str) -> Product:
        return self.store.get_product(product_id)

    def find_by_barcode(self, barcode: str) -> Product | None:
        return self.store.find_by_barcode(barcode)

    def search(self, text: str) -> list[Product]:
        return self.store.search_products(text)

    def list_active(self) -> list[Product]:
        return self.store.list_products(active_only=True)

    def associate_model_class(self, product_id: str, model_name: str, class_label: str) -> None:
        self.store.associate_model_class(product_id, model_name, class_label)

    def find_by_model_class(self, model_name: str, class_label: str) -> Product | None:
        return self.store.find_by_model_class(model_name, class_label)
