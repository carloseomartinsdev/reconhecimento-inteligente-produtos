"""Testes do catálogo, do banco e do motor de preços.

Todos os valores numéricos são sintéticos. Eles não são preços de mercado.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from catalog.identity import IdentityError, commercial_key
from catalog.service import Catalog
from database.store import Store, StoreError
from pricing.engine import CLASSIFIED, INSUFFICIENT, LEGAL_LIMITATION
from pricing.money import MoneyError, parse_price
from pricing.policy import PricePolicy, classify_percent
from pricing.statistics import mean, median, population_std, quartile, summarize
from utils.config import load_config


def small_policy(**overrides: object) -> PricePolicy:
    payload = dict(
        excellent_below=Decimal("-10"),
        good_below=Decimal("-3"),
        within_until=Decimal("5"),
        above_until=Decimal("15"),
        min_records=3,
        max_age_days=90,
        min_establishments=2,
        regular_only=True,
    )
    payload.update(overrides)
    return PricePolicy(**payload)  # type: ignore[arg-type]


def test_commercial_identity_keeps_pack_sizes_apart() -> None:
    small = commercial_key("Marca Sintética", "Original", "350", "ml")
    large = commercial_key("marca sintetica", "original", Decimal("1000"), "ML")
    assert small != large
    assert commercial_key("Marca Sintética", "Original", "350.000", "ml") == small


def test_barcode_is_optional_and_not_invented() -> None:
    from catalog.identity import normalize_barcode

    assert normalize_barcode(None) is None
    assert normalize_barcode("  ") is None
    assert normalize_barcode("7891000315507") == "7891000315507"
    with pytest.raises(IdentityError):
        normalize_barcode("123")


def test_catalog_register_search_update_and_model_link(tmp_path) -> None:
    with Store(tmp_path / "sintetico.sqlite") as store:
        catalog = Catalog(store)
        first = catalog.register(
            name="Produto sintético A",
            brand="Marca Sintética",
            category="Teste",
            variant="Original",
            quantity="350",
            unit="ml",
        )
        second = catalog.register(
            name="Produto sintético B",
            brand="Marca Sintética",
            category="Teste",
            variant="Original",
            quantity="1",
            unit="L",
        )
        assert first.id == "BR0001"
        assert second.id == "BR0002"
        assert first.commercial_key != second.commercial_key
        found = catalog.search("sintético a")
        assert [item.id for item in found] == ["BR0001"]
        updated = catalog.update("BR0001", name="Produto sintético A atualizado")
        assert updated.name == "Produto sintético A atualizado"
        assert catalog.get("BR0001").id == "BR0001"
        catalog.associate_model_class("BR0001", "mobilenet_v3_large", "classe-teste")
        assert catalog.find_by_model_class("mobilenet_v3_large", "classe-teste").id == "BR0001"
        with pytest.raises(StoreError):
            catalog.register(
                name="Repetido",
                brand="Marca Sintética",
                category="Teste",
                variant="Original",
                quantity="350",
                unit="ml",
            )


def test_barcode_lookup_and_establishment(tmp_path) -> None:
    with Store(tmp_path / "sintetico.sqlite") as store:
        product = store.register_product(
            name="Item sintético",
            brand="Marca Sintética",
            category="Teste",
            quantity=1,
            unit="un",
            barcode="00000000",
        )
        assert store.find_by_barcode("00000000").id == product.id
        place = store.register_establishment(name="Loja sintética", city="Campinas", state="sp", neighborhood="Centro")
        assert place.state == "SP"
        assert place.neighborhood == "Centro"
        with pytest.raises(StoreError):
            store.register_establishment(name="Loja", city="Campinas", state="XX")


def test_invalid_and_negative_prices_are_rejected(tmp_path) -> None:
    with Store(tmp_path / "sintetico.sqlite") as store:
        product = store.register_product(
            name="Item sintético", brand="Marca", category="Teste", quantity=1, unit="un"
        )
        place = store.register_establishment(name="Loja sintética", city="Campinas", state="SP")
        with pytest.raises(MoneyError):
            store.register_price(
                product_id=product.id,
                establishment_id=place.id,
                price="-1,00",
                observed_on=date.today(),
                source_code="manual",
                price_type="regular",
            )
        with pytest.raises(MoneyError):
            store.register_price(
                product_id=product.id,
                establishment_id=place.id,
                price="abc",
                observed_on=date.today(),
                source_code="manual",
                price_type="regular",
            )
        with pytest.raises(MoneyError):
            parse_price(1.29)
        saved = store.register_price(
            product_id=product.id,
            establishment_id=place.id,
            price="0,10",
            observed_on=date.today(),
            source_code="manual",
            price_type="regular",
        )
        assert saved.price == Decimal("0.10")
        assert isinstance(saved.price, Decimal)


def test_statistics_use_decimal_and_known_quartiles() -> None:
    values = [Decimal(number) for number in (1, 2, 3, 4, 5)]
    assert mean(values) == Decimal("3")
    assert median(values) == Decimal("3")
    assert quartile(values, Decimal("0.25")) == Decimal("2")
    assert quartile(values, Decimal("0.75")) == Decimal("4")
    assert population_std(values) == (Decimal(2).sqrt())
    even = [Decimal("1"), Decimal("2"), Decimal("3"), Decimal("4")]
    assert median(even) == Decimal("2.5")
    assert summarize([])["count"] == 0
    assert mean([Decimal("0.10"), Decimal("0.20")]) == Decimal("0.15")


def test_classification_boundaries() -> None:
    policy = small_policy()
    assert classify_percent(Decimal("-10.01"), policy) == "Excelente preço"
    assert classify_percent(Decimal("-10"), policy) == "Bom preço"
    assert classify_percent(Decimal("-3.01"), policy) == "Bom preço"
    assert classify_percent(Decimal("-3"), policy) == "Dentro da média"
    assert classify_percent(Decimal("5"), policy) == "Dentro da média"
    assert classify_percent(Decimal("5.01"), policy) == "Acima da média"
    assert classify_percent(Decimal("15"), policy) == "Acima da média"
    assert classify_percent(Decimal("15.01"), policy) == "Muito acima da média"


def test_median_is_the_reference_when_an_outlier_moves_the_mean(tmp_path) -> None:
    with Store(tmp_path / "sintetico.sqlite") as store:
        product = store.register_product(
            name="Item sintético", brand="Marca Sintética", category="Teste", quantity=1, unit="un"
        )
        places = [
            store.register_establishment(name=f"Loja sintética {index}", city="Campinas", state="SP")
            for index in range(3)
        ]
        for price, place in (("10.00", places[0]), ("10.00", places[1]), ("10.00", places[0]), ("10.00", places[2]), ("100.00", places[2])):
            store.register_price(
                product_id=product.id,
                establishment_id=place.id,
                price=price,
                observed_on=date.today(),
                source_code="manual",
                price_type="regular",
            )
        from pricing.engine import PriceEngine

        report = PriceEngine(store, small_policy(min_records=5, min_establishments=3)).compare(
            product_id=product.id,
            informed_price="10,00",
            state="SP",
            city="Campinas",
        )
        assert report.status == CLASSIFIED
        assert report.median == Decimal("10")
        assert report.mean == Decimal("28")
        assert report.percent_vs_median == Decimal("0")
        assert report.percent_vs_mean != report.percent_vs_median
        assert report.classification == "Dentro da média"
        assert LEGAL_LIMITATION in report.limitations


def test_insufficient_data_old_records_promotions_and_region(tmp_path) -> None:
    with Store(tmp_path / "sintetico.sqlite") as store:
        product = store.register_product(
            name="Item sintético", brand="Marca Sintética", category="Teste", quantity=1, unit="un"
        )
        place = store.register_establishment(name="Loja sintética", city="Campinas", state="SP")
        other = store.register_establishment(name="Loja de outra cidade", city="Santos", state="SP")
        policy = PricePolicy.from_mapping(load_config("pricing.yaml"))
        from pricing.engine import PriceEngine

        engine = PriceEngine(store, policy)
        empty = engine.compare(product_id=product.id, informed_price="10,00", state="SP", city="Campinas")
        assert empty.status == INSUFFICIENT
        assert empty.classification is None
        assert "poucos_registros" in empty.reasons
        for index in range(5):
            store.register_price(
                product_id=product.id,
                establishment_id=place.id,
                price="9,00",
                observed_on=date.today() - timedelta(days=200),
                source_code="manual",
                price_type="regular",
            )
        stale = engine.compare(product_id=product.id, informed_price="10,00", state="SP", city="Campinas")
        assert stale.status == INSUFFICIENT
        assert "registros_desatualizados" in stale.reasons
        store.register_price(
            product_id=product.id,
            establishment_id=other.id,
            price="1,00",
            observed_on=date.today(),
            source_code="manual",
            price_type="promotional",
            offer_conditions="sintético, somente para o teste",
        )
        promo = engine.compare(product_id=product.id, informed_price="10,00", state="SP", city="Santos")
        assert promo.status == INSUFFICIENT
        assert "sem_preco_regular" in promo.reasons or "poucos_registros" in promo.reasons
        outside = engine.compare(product_id=product.id, informed_price="10,00", state="RJ", city="Campinas")
        assert outside.status == INSUFFICIENT
        assert "nenhum_registro_na_regiao" in outside.reasons
        missing_region = engine.compare(product_id=product.id, informed_price="10,00", state=None)
        assert missing_region.status == INSUFFICIENT
        assert "regiao_nao_informada" in missing_region.reasons


def test_unit_prices_are_not_mixed_with_package_prices(tmp_path) -> None:
    with Store(tmp_path / "sintetico.sqlite") as store:
        can = store.register_product(
            name="Embalagem sintética pequena",
            brand="Marca Sintética",
            category="Teste",
            variant="Original",
            quantity="350",
            unit="ml",
        )
        bottle = store.register_product(
            name="Embalagem sintética grande",
            brand="Marca Sintética",
            category="Teste",
            variant="Original",
            quantity="1",
            unit="L",
        )
        unrelated = store.register_product(
            name="Outro sintético",
            brand="Outra Marca",
            category="Teste",
            variant="Original",
            quantity="350",
            unit="ml",
        )
        places = [
            store.register_establishment(name=f"Loja sintética {index}", city="Campinas", state="SP")
            for index in range(2)
        ]
        store.register_price(
            product_id=can.id, establishment_id=places[0].id, price="3,50",
            observed_on=date.today(), source_code="manual", price_type="regular",
        )
        store.register_price(
            product_id=bottle.id, establishment_id=places[1].id, price="8,00",
            observed_on=date.today(), source_code="manual", price_type="regular",
        )
        store.register_price(
            product_id=unrelated.id, establishment_id=places[0].id, price="1,00",
            observed_on=date.today(), source_code="manual", price_type="regular",
        )
        from pricing.engine import PriceEngine
        from pricing.units import package_to_unit_price

        unit_price, unit_name = package_to_unit_price(Decimal("3.50"), Decimal("350"), "ml")
        assert unit_name == "L"
        assert unit_price == Decimal("10")
        engine = PriceEngine(store, small_policy(min_records=1, min_establishments=1))
        package_report = engine.compare(
            product_id=can.id, informed_price="3,50", state="SP", city="Campinas", basis="package"
        )
        assert package_report.status == CLASSIFIED
        assert package_report.product_ids == [can.id]
        assert package_report.median == Decimal("3.50")
        refused = engine.compare(
            product_id=can.id, informed_price="3,50", state="SP", city="Campinas", basis="unit"
        )
        assert refused.status == INSUFFICIENT
        assert "comparacao_por_unidade_nao_confirmada" in refused.reasons
        confirmed = engine.compare(
            product_id=can.id,
            informed_price="3,50",
            state="SP",
            city="Campinas",
            basis="unit",
            confirm_unit_comparison=True,
        )
        assert confirmed.status == CLASSIFIED
        assert confirmed.price_basis == "unidade"
        assert set(confirmed.product_ids) == {can.id, bottle.id}
        assert confirmed.median == Decimal("9")
        assert confirmed.package_price == Decimal("3.50")
        assert confirmed.informed_price == Decimal("10")


def test_pending_records_do_not_classify(tmp_path) -> None:
    with Store(tmp_path / "sintetico.sqlite") as store:
        product = store.register_product(
            name="Item sintético", brand="Marca", category="Teste", quantity=1, unit="un"
        )
        place = store.register_establishment(name="Loja sintética", city="Campinas", state="SP")
        another = store.register_establishment(name="Segunda loja sintética", city="Campinas", state="SP")
        for establishment in (place, another, place):
            store.register_price(
                product_id=product.id,
                establishment_id=establishment.id,
                price="4,00",
                observed_on=date.today(),
                source_code="consumer_report",
                price_type="regular",
                validation_status="pending",
            )
        from pricing.engine import PriceEngine

        report = PriceEngine(store, small_policy()).compare(
            product_id=product.id, informed_price="4,00", state="SP", city="Campinas"
        )
        assert report.status == INSUFFICIENT
        assert "registros_nao_validados" in report.reasons


def test_demo_prices_are_marked_and_not_duplicated(tmp_path) -> None:
    from pricing.test_prices import TEST_OFFER, ensure_test_prices

    with Store(tmp_path / "sintetico.sqlite") as store:
        product = store.register_product(
            name="Arroz sintético", brand="Marca", category="Arroz", quantity=5, unit="kg"
        )
        first = ensure_test_prices(store)
        second = ensure_test_prices(store)
        records = store.list_prices(product.id)
        assert first == 5
        assert second == 0
        assert len(records) == 5
        assert {record.offer_conditions for record in records} == {TEST_OFFER}
        assert {record.validation_status for record in records} == {"valid"}
        assert len({record.establishment_id for record in records}) == 5
