"""Comparação do preço informado com os registros válidos.

A região pedida não é alargada quando a amostra fica pequena.
A classificação descreve a posição estatística e não uma conclusão jurídica.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from database.models import PriceRecord, Product
from database.store import Store
from pricing.money import parse_price
from pricing.policy import PricePolicy, classify_percent
from pricing.statistics import percent_difference, summarize
from pricing.units import base_quantity, package_to_unit_price

LEGAL_LIMITATION = (
    "A classificação compara o preço informado com a mediana dos registros válidos. "
    "Ela não apura infração, superfaturamento ilegal ou prática abusiva."
)
REGION_LIMITATION = "A região consultada não foi ampliada automaticamente."
INSUFFICIENT = "DADOS_INSUFICIENTES"
CLASSIFIED = "CLASSIFICADO"


@dataclass
class ComparisonReport:
    status: str
    classification: str | None
    package_price: Decimal
    informed_price: Decimal
    price_basis: str
    unit_name: str | None
    count: int
    establishment_count: int
    minimum: Decimal | None
    maximum: Decimal | None
    mean: Decimal | None
    median: Decimal | None
    population_std: Decimal | None
    q1: Decimal | None
    q3: Decimal | None
    percent_vs_mean: Decimal | None
    percent_vs_median: Decimal | None
    latest_observation: date | None
    region_state: str | None
    region_city: str | None
    promotional_excluded: bool
    product_ids: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


class PriceEngine:
    def __init__(self, store: Store, policy: PricePolicy):
        self.store = store
        self.policy = policy

    def compare(
        self,
        *,
        product_id: str,
        informed_price: Decimal | int | str,
        state: str | None,
        city: str | None = None,
        as_of: date | None = None,
        basis: str = "package",
        confirm_unit_comparison: bool = False,
    ) -> ComparisonReport:
        price = parse_price(informed_price)
        reference_day = as_of or date.today()
        product = self.store.get_product(product_id)
        limitations = [LEGAL_LIMITATION, REGION_LIMITATION]
        if state is None or state.strip() == "":
            return self._insufficient(
                price,
                price,
                basis,
                None,
                None,
                [],
                ["regiao_nao_informada"],
                limitations,
                self.policy.regular_only,
            )
        uf = state.strip().upper()
        city_label = None if city is None or city.strip() == "" else city.strip()
        city_filter = None if city_label is None else city_label.casefold()
        products = self._products_in_scope(product, basis, confirm_unit_comparison)
        if products is None:
            return self._insufficient(
                price,
                price,
                basis,
                uf,
                city_label,
                [product.id],
                ["comparacao_por_unidade_nao_confirmada"],
                limitations,
                self.policy.regular_only,
            )
        records = self.store.list_prices_for_products([item.id for item in products])
        informed_value, unit_name = self._informed_value(price, product, basis)
        usable, reasons = self._select(records, products, uf, city_filter, reference_day, basis)
        if reasons:
            return self._insufficient(
                price,
                informed_value,
                basis,
                uf,
                city_label,
                [item.id for item in products],
                reasons,
                limitations,
                self.policy.regular_only,
                count=len(usable),
                establishment_count=len({item.establishment_id for item in usable}),
                latest=max((item.observed_on for item in usable), default=None),
                unit_name=unit_name,
            )
        values = [self._value(item, products, basis) for item in usable]
        stats = summarize(values)
        median_value = stats["median"]
        mean_value = stats["mean"]
        assert isinstance(median_value, Decimal)
        assert isinstance(mean_value, Decimal)
        percent_median = percent_difference(informed_value, median_value)
        percent_mean = percent_difference(informed_value, mean_value)
        assert percent_median is not None
        return ComparisonReport(
            status=CLASSIFIED,
            classification=classify_percent(percent_median, self.policy),
            package_price=price,
            informed_price=informed_value,
            price_basis="unidade" if basis == "unit" else "embalagem",
            unit_name=unit_name,
            count=len(values),
            establishment_count=len({item.establishment_id for item in usable}),
            minimum=stats["minimum"],  # type: ignore[arg-type]
            maximum=stats["maximum"],  # type: ignore[arg-type]
            mean=mean_value,
            median=median_value,
            population_std=stats["population_std"],  # type: ignore[arg-type]
            q1=stats["q1"],  # type: ignore[arg-type]
            q3=stats["q3"],  # type: ignore[arg-type]
            percent_vs_mean=percent_mean,
            percent_vs_median=percent_median,
            latest_observation=max(item.observed_on for item in usable),
            region_state=uf,
            region_city=city_label,
            promotional_excluded=self.policy.regular_only,
            product_ids=[item.id for item in products],
            limitations=limitations,
        )

    def _products_in_scope(
        self,
        product: Product,
        basis: str,
        confirm_unit_comparison: bool,
    ) -> list[Product] | None:
        if basis == "package":
            return [product]
        if basis != "unit":
            raise ValueError("A base da comparação é 'package' ou 'unit'.")
        if not confirm_unit_comparison:
            return None
        target_base = base_quantity(product.quantity, product.unit)[1]
        selected = []
        for candidate in self.store.products_with_same_brand_variant(product):
            if base_quantity(candidate.quantity, candidate.unit)[1] == target_base:
                selected.append(candidate)
        return selected or [product]

    def _select(
        self,
        records: list[PriceRecord],
        products: list[Product],
        state: str,
        city_filter: str | None,
        as_of: date,
        basis: str,
    ) -> tuple[list[PriceRecord], list[str]]:
        del basis
        in_region = [
            record
            for record in records
            if record.state == state and (city_filter is None or record.city.casefold() == city_filter)
        ]
        valid = [record for record in in_region if record.validation_status == "valid"]
        cutoff = as_of - timedelta(days=self.policy.max_age_days)
        recent = [record for record in valid if record.observed_on >= cutoff]
        if self.policy.regular_only:
            typed = [record for record in recent if record.price_type == "regular"]
        else:
            typed = recent
        reasons: list[str] = []
        if records and not in_region:
            reasons.append("nenhum_registro_na_regiao")
        if in_region and not valid:
            reasons.append("registros_nao_validados")
        if valid and not recent:
            reasons.append("registros_desatualizados")
        if recent and self.policy.regular_only and not typed:
            reasons.append("sem_preco_regular")
        if len(typed) < self.policy.min_records:
            reasons.append("poucos_registros")
        if len({record.establishment_id for record in typed}) < self.policy.min_establishments:
            reasons.append("poucos_estabelecimentos")
        if any(base_quantity(product.quantity, product.unit)[1] != base_quantity(products[0].quantity, products[0].unit)[1] for product in products):
            reasons.append("unidades_incompativeis")
        return typed, reasons

    def _value(self, record: PriceRecord, products: list[Product], basis: str) -> Decimal:
        if basis == "package":
            return record.price
        product = next(item for item in products if item.id == record.product_id)
        return package_to_unit_price(record.price, product.quantity, product.unit)[0]

    def _informed_value(self, price: Decimal, product: Product, basis: str) -> tuple[Decimal, str | None]:
        if basis == "package":
            return price, None
        unit_price, unit_name = package_to_unit_price(price, product.quantity, product.unit)
        return unit_price, unit_name

    def _insufficient(
        self,
        package_price: Decimal,
        informed_price: Decimal,
        basis: str,
        state: str | None,
        city: str | None,
        product_ids: list[str],
        reasons: list[str],
        limitations: list[str],
        promotional_excluded: bool,
        count: int = 0,
        establishment_count: int = 0,
        latest: date | None = None,
        unit_name: str | None = None,
    ) -> ComparisonReport:
        return ComparisonReport(
            status=INSUFFICIENT,
            classification=None,
            package_price=package_price,
            informed_price=informed_price,
            price_basis="unidade" if basis == "unit" else "embalagem",
            unit_name=unit_name,
            count=count,
            establishment_count=establishment_count,
            minimum=None,
            maximum=None,
            mean=None,
            median=None,
            population_std=None,
            q1=None,
            q3=None,
            percent_vs_mean=None,
            percent_vs_median=None,
            latest_observation=latest,
            region_state=state,
            region_city=city,
            promotional_excluded=promotional_excluded,
            product_ids=product_ids,
            reasons=reasons,
            limitations=limitations,
        )
