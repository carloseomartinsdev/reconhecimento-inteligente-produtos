"""Persistência SQLite do catálogo e dos preços."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from catalog.identity import (
    IdentityError,
    canonical_unit,
    commercial_key,
    normalize_barcode,
    parse_quantity,
    quantity_text,
)
from database.models import Establishment, PriceRecord, Product
from database.schema import init_schema
from pricing.money import format_price, parse_price

PRICE_TYPES = ("regular", "promotional", "loyalty", "other")
VALIDATION_STATUSES = ("pending", "valid", "invalid")
UF = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
    "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}


class StoreError(ValueError):
    """Violação de cadastro ou de integridade do banco local."""


class Store:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        init_schema(self.connection)

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> Store:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def register_product(
        self,
        *,
        name: str,
        brand: str,
        category: str,
        variant: str = "",
        quantity: Decimal | int | str,
        unit: str,
        packaging: str = "",
        barcode: str | None = None,
        reference_image: str | None = None,
        active: bool = True,
        product_id: str | None = None,
    ) -> Product:
        self._require_text(name, "nome")
        self._require_text(brand, "marca")
        self._require_text(category, "categoria")
        key = commercial_key(brand, variant, quantity, unit, name, packaging)
        parsed_barcode = normalize_barcode(barcode)
        identifier = product_id or self._next_product_id()
        if not identifier.startswith("BR") or not identifier[2:].isdigit():
            raise IdentityError("O identificador interno precisa ter o formato BR seguido de dígitos.")
        try:
            self.connection.execute(
                """
                INSERT INTO products (
                    id, name, brand, category, variant, quantity, unit, packaging, barcode,
                    reference_image, active, commercial_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    identifier,
                    name.strip(),
                    brand.strip(),
                    category.strip(),
                    variant.strip(),
                    quantity_text(parse_quantity(quantity)),
                    canonical_unit(unit),
                    packaging.strip(),
                    parsed_barcode,
                    reference_image,
                    1 if active else 0,
                    key,
                ),
            )
            self.connection.commit()
        except sqlite3.IntegrityError as exc:
            raise StoreError("Já existe produto com a mesma identidade comercial ou o mesmo código de barras.") from exc
        return self.get_product(identifier)

    def update_product(self, product_id: str, **changes: object) -> Product:
        current = self.get_product(product_id)
        name = str(changes.get("name", current.name))
        brand = str(changes.get("brand", current.brand))
        category = str(changes.get("category", current.category))
        variant = str(changes.get("variant", current.variant))
        quantity = changes.get("quantity", current.quantity)
        unit = str(changes.get("unit", current.unit))
        packaging = str(changes.get("packaging", current.packaging))
        barcode = changes.get("barcode", current.barcode)
        reference_image = changes.get("reference_image", current.reference_image)
        active = bool(changes.get("active", current.active))
        key = commercial_key(brand, variant, quantity, unit, name, packaging)  # type: ignore[arg-type]
        parsed_barcode = normalize_barcode(None if barcode is None else str(barcode))
        try:
            self.connection.execute(
                """
                UPDATE products
                SET name = ?, brand = ?, category = ?, variant = ?, quantity = ?, unit = ?,
                    packaging = ?, barcode = ?, reference_image = ?, active = ?, commercial_key = ?
                WHERE id = ?
                """,
                (
                    name.strip(),
                    brand.strip(),
                    category.strip(),
                    variant.strip(),
                    quantity_text(parse_quantity(quantity)),  # type: ignore[arg-type]
                    canonical_unit(unit),
                    packaging.strip(),
                    parsed_barcode,
                    reference_image,
                    1 if active else 0,
                    key,
                    product_id,
                ),
            )
            self.connection.commit()
        except sqlite3.IntegrityError as exc:
            raise StoreError("A alteração colide com outro produto já cadastrado.") from exc
        return self.get_product(product_id)

    def get_product(self, product_id: str) -> Product:
        row = self.connection.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if row is None:
            raise StoreError(f"Produto não encontrado: {product_id}.")
        return self._product(row)

    def find_by_barcode(self, barcode: str) -> Product | None:
        normalized = normalize_barcode(barcode)
        if normalized is None:
            return None
        row = self.connection.execute("SELECT * FROM products WHERE barcode = ?", (normalized,)).fetchone()
        return None if row is None else self._product(row)

    def search_products(self, text: str, include_inactive: bool = False) -> list[Product]:
        needle = text.strip().casefold()
        if needle == "":
            return []
        rows = self.connection.execute("SELECT * FROM products ORDER BY name").fetchall()
        found = []
        for row in rows:
            product = self._product(row)
            if not include_inactive and not product.active:
                continue
            haystack = f"{product.name} {product.brand} {product.variant} {product.category}".casefold()
            if needle in haystack:
                found.append(product)
        return found

    def list_products(self, active_only: bool = True) -> list[Product]:
        rows = self.connection.execute("SELECT * FROM products ORDER BY id").fetchall()
        products = [self._product(row) for row in rows]
        if active_only:
            return [product for product in products if product.active]
        return products

    def associate_model_class(self, product_id: str, model_name: str, class_label: str) -> None:
        self.get_product(product_id)
        self._require_text(model_name, "modelo")
        self._require_text(class_label, "classe")
        self.connection.execute(
            """
            INSERT INTO model_class_links (model_name, class_label, product_id)
            VALUES (?, ?, ?)
            ON CONFLICT(model_name, class_label) DO UPDATE SET product_id = excluded.product_id
            """,
            (model_name.strip(), class_label.strip(), product_id),
        )
        self.connection.commit()

    def find_by_model_class(self, model_name: str, class_label: str) -> Product | None:
        row = self.connection.execute(
            """
            SELECT products.*
            FROM model_class_links
            JOIN products ON products.id = model_class_links.product_id
            WHERE model_class_links.model_name = ? AND model_class_links.class_label = ?
            """,
            (model_name, class_label),
        ).fetchone()
        return None if row is None else self._product(row)

    def register_establishment(
        self,
        *,
        name: str,
        city: str,
        state: str,
        neighborhood: str | None = None,
        external_id: str | None = None,
        active: bool = True,
    ) -> Establishment:
        self._require_text(name, "nome do estabelecimento")
        self._require_text(city, "cidade")
        uf = state.strip().upper()
        if uf not in UF:
            raise StoreError("Estado precisa ser a sigla de uma UF brasileira.")
        external = None if external_id is None or str(external_id).strip() == "" else str(external_id).strip()
        try:
            cursor = self.connection.execute(
                """
                INSERT INTO establishments (name, city, state, neighborhood, external_id, active)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    name.strip(),
                    city.strip(),
                    uf,
                    None if neighborhood is None or neighborhood.strip() == "" else neighborhood.strip(),
                    external,
                    1 if active else 0,
                ),
            )
            self.connection.commit()
        except sqlite3.IntegrityError as exc:
            raise StoreError("Identificador externo de estabelecimento já cadastrado.") from exc
        return self.get_establishment(int(cursor.lastrowid))

    def get_establishment(self, establishment_id: int) -> Establishment:
        row = self.connection.execute(
            "SELECT * FROM establishments WHERE id = ?",
            (establishment_id,),
        ).fetchone()
        if row is None:
            raise StoreError(f"Estabelecimento não encontrado: {establishment_id}.")
        return self._establishment(row)

    def register_price(
        self,
        *,
        product_id: str,
        establishment_id: int,
        price: Decimal | int | str,
        observed_on: date,
        source_code: str,
        price_type: str,
        offer_conditions: str = "",
        validation_status: str = "valid",
        as_of: date | None = None,
    ) -> PriceRecord:
        self.get_product(product_id)
        self.get_establishment(establishment_id)
        parsed = parse_price(price)
        if price_type not in PRICE_TYPES:
            raise StoreError(f"Tipo de preço não previsto: {price_type}.")
        if validation_status not in VALIDATION_STATUSES:
            raise StoreError(f"Status de validação não previsto: {validation_status}.")
        source = self.connection.execute("SELECT id FROM sources WHERE code = ?", (source_code,)).fetchone()
        if source is None:
            raise StoreError(f"Fonte não cadastrada: {source_code}.")
        limit = as_of or date.today()
        if observed_on > limit:
            raise StoreError("A data da observação não pode ser posterior à data de referência.")
        recorded_at = datetime.now(timezone.utc).replace(microsecond=0)
        cursor = self.connection.execute(
            """
            INSERT INTO price_records (
                product_id, establishment_id, price, observed_on, recorded_at,
                source_id, price_type, offer_conditions, validation_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product_id,
                establishment_id,
                format_price(parsed),
                observed_on.isoformat(),
                recorded_at.isoformat(),
                int(source["id"]),
                price_type,
                offer_conditions.strip(),
                validation_status,
            ),
        )
        self.connection.commit()
        return self.get_price(int(cursor.lastrowid))

    def get_price(self, price_id: int) -> PriceRecord:
        row = self._price_query("WHERE price_records.id = ?", (price_id,))
        if not row:
            raise StoreError(f"Registro de preço não encontrado: {price_id}.")
        return row[0]

    def list_prices(self, product_id: str) -> list[PriceRecord]:
        return self._price_query("WHERE price_records.product_id = ? ORDER BY observed_on", (product_id,))

    def list_establishments(self, active_only: bool = True) -> list[Establishment]:
        rows = self.connection.execute("SELECT * FROM establishments ORDER BY name").fetchall()
        establishments = [self._establishment(row) for row in rows]
        if active_only:
            return [item for item in establishments if item.active]
        return establishments

    def list_prices_for_products(self, product_ids: list[str]) -> list[PriceRecord]:
        if not product_ids:
            return []
        marks = ", ".join("?" for _ in product_ids)
        return self._price_query(
            f"WHERE price_records.product_id IN ({marks}) ORDER BY observed_on",
            tuple(product_ids),
        )

    def products_with_same_brand_variant(self, product: Product) -> list[Product]:
        rows = self.connection.execute("SELECT * FROM products WHERE active = 1").fetchall()
        selected = []
        for row in rows:
            candidate = self._product(row)
            if commercial_key(candidate.brand, candidate.variant, candidate.quantity, candidate.unit).split("|")[:2] == (
                commercial_key(product.brand, product.variant, product.quantity, product.unit).split("|")[:2]
            ):
                selected.append(candidate)
        return selected

    def _price_query(self, clause: str, parameters: tuple[object, ...]) -> list[PriceRecord]:
        rows = self.connection.execute(
            f"""
            SELECT price_records.*, sources.code AS source_code, establishments.city, establishments.state
            FROM price_records
            JOIN sources ON sources.id = price_records.source_id
            JOIN establishments ON establishments.id = price_records.establishment_id
            {clause}
            """,
            parameters,
        ).fetchall()
        return [self._price(row) for row in rows]

    def _next_product_id(self) -> str:
        rows = self.connection.execute("SELECT id FROM products WHERE id LIKE 'BR%'").fetchall()
        highest = 0
        for row in rows:
            suffix = str(row["id"])[2:]
            if suffix.isdigit():
                highest = max(highest, int(suffix))
        return f"BR{highest + 1:04d}"

    def _product(self, row: sqlite3.Row) -> Product:
        return Product(
            id=row["id"],
            name=row["name"],
            brand=row["brand"],
            category=row["category"],
            variant=row["variant"],
            quantity=Decimal(row["quantity"]),
            unit=row["unit"],
            packaging=str(row["packaging"] or ""),
            barcode=row["barcode"],
            reference_image=row["reference_image"],
            active=bool(row["active"]),
            commercial_key=row["commercial_key"],
        )

    def _establishment(self, row: sqlite3.Row) -> Establishment:
        return Establishment(
            id=int(row["id"]),
            name=row["name"],
            city=row["city"],
            state=row["state"],
            neighborhood=row["neighborhood"],
            external_id=row["external_id"],
            active=bool(row["active"]),
        )

    def _price(self, row: sqlite3.Row) -> PriceRecord:
        return PriceRecord(
            id=int(row["id"]),
            product_id=row["product_id"],
            establishment_id=int(row["establishment_id"]),
            price=Decimal(row["price"]),
            observed_on=date.fromisoformat(row["observed_on"]),
            recorded_at=datetime.fromisoformat(row["recorded_at"]),
            source_code=row["source_code"],
            price_type=row["price_type"],
            offer_conditions=row["offer_conditions"],
            validation_status=row["validation_status"],
            city=row["city"],
            state=row["state"],
        )

    @staticmethod
    def _require_text(value: str, field: str) -> None:
        if value is None or str(value).strip() == "":
            raise IdentityError(f"O campo {field} é obrigatório.")
