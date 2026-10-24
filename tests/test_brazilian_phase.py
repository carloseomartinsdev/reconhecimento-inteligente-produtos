"""Fase 2.2: catálogo rastreável, validação e travas de treino.

Os produtos sintéticos deste arquivo não são o catálogo brasileiro.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image

from catalog.identity import commercial_key
from catalog.import_brazilian import import_products
from classification.augment import build_brazilian_train_transform
from classification.candidates import load_checkpoint, top_candidates
from classification.embeddings import embedding_status
from classification.models import trainable_parameters
from classification.transfer import (
    apply_stage,
    assert_ready_for_training,
    build_transfer_classifier,
    parameter_groups,
    weight_reference,
)
from database.store import Store
from datasets.brazilian_validate import validate_dataset, write_report
from datasets.off_record import packaging_from_text, parse_quantity_text, variant_from_name
from evaluation.recognition import exploratory_group_split, recognition_report, same_protocol, topk_accuracy
from preprocessing.transforms import build_eval_transform
from pricing.connectors import CommercialScrapingConnector, ManualConnector


def test_quantity_variant_and_packaging_come_from_source_text() -> None:
    assert parse_quantity_text("500 g") == (parse_quantity_text("500 g")[0], "g")
    assert parse_quantity_text("1 kg e 500 g") is None
    assert parse_quantity_text(None) is None
    variant, evidence = variant_from_name("Café Torrado e Moído Tradicional")
    assert fold_has(variant, "torrado")
    assert evidence == "trecho_do_nome_na_fonte"
    assert variant_from_name("Produto sem termo conhecido") == ("", None)
    packaging = packaging_from_text(None, "Arroz pacote 1 kg")
    assert packaging == ("Pacote", "nome_na_fonte")
    assert packaging_from_text(None, "sem indicacao") is None


def fold_has(value: str, token: str) -> bool:
    return token in value.casefold()


def test_packaging_extends_identity_without_changing_the_old_key() -> None:
    old = commercial_key("Marca Sintética", "Original", "350", "ml")
    newer = commercial_key("Marca Sintética", "Original", "350", "ml", "Nome sintético", "Lata")
    assert old.count("|") == 3
    assert newer != old


def test_import_uses_only_validated_rows(tmp_path: Path) -> None:
    catalog = tmp_path / "products.json"
    catalog.write_text(
        json.dumps(
            {
                "produtos": [
                    {
                        "id": "BR0001",
                        "nome": "Item sintético",
                        "marca": "Marca Sintética",
                        "categoria": "Teste",
                        "variante": "",
                        "quantidade": "500",
                        "unidade": "g",
                        "tipo_embalagem": "Pacote",
                        "codigo_barras": "00000000",
                        "status_comercial": "validado",
                        "ativo": True,
                    },
                    {
                        "id": "BR0002",
                        "nome": "Item incompleto",
                        "marca": "Outra",
                        "categoria": "Teste",
                        "quantidade": "1",
                        "unidade": "kg",
                        "status_comercial": "rejeitado",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    store = Store(tmp_path / "precos.sqlite")
    assert import_products(store, catalog) == 1
    assert import_products(store, catalog) == 0
    product = store.get_product("BR0001")
    assert product.packaging == "Pacote"
    assert product.barcode == "00000000"


def _jpeg(path: Path, size: tuple[int, int], color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, format="JPEG")


def test_validator_rejects_small_corrupt_unknown_and_duplicate(tmp_path: Path) -> None:
    root = tmp_path / "brazilian_products"
    metadata = root / "metadata"
    metadata.mkdir(parents=True)
    good = root / "images" / "BR0001" / "1.jpg"
    small = root / "images" / "BR0001" / "2.jpg"
    copy = root / "images" / "BR0001" / "3.jpg"
    _jpeg(good, (300, 280), (20, 40, 60))
    _jpeg(small, (40, 40), (255, 0, 0))
    copy.write_bytes(good.read_bytes())
    (root / "images" / "BR0001" / "4.jpg").write_bytes(b"nao e imagem")
    products = {
        "produtos": [
            {
                "id": "BR0001",
                "nome": "Sintético",
                "categoria": "Arroz",
                "status_comercial": "validado",
            }
        ]
    }
    (metadata / "products.json").write_text(json.dumps(products), encoding="utf-8")
    rows = [
        _row("BR0001", "images/BR0001/1.jpg", "CC BY-SA", "sim"),
        _row("BR0001", "images/BR0001/2.jpg", "CC BY-SA", "sim"),
        _row("BR0001", "images/BR0001/3.jpg", "CC BY-SA", "sim"),
        _row("BR0001", "images/BR0001/4.jpg", "CC BY-SA", "sim"),
        _row("BR0001", "images/BR0001/ausente.jpg", "desconhecida", "nao"),
    ]
    with (metadata / "image_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = validate_dataset(root)
    reasons = {item["arquivo"]: [reason["code"] for reason in item["motivos"]] for item in report["imagens"]}
    assert reasons["images/BR0001/2.jpg"] == ["resolucao_insuficiente"]
    assert "arquivo_corrompido" in reasons["images/BR0001/4.jpg"]
    assert "duplicata_exata" in reasons["images/BR0001/3.jpg"]
    assert "licenca_desconhecida" in reasons["images/BR0001/ausente.jpg"]
    assert "sem_autorizacao" in reasons["images/BR0001/ausente.jpg"]
    assert report["completo"] is False
    assert report["produtos"][0]["atingiu_minimo"] is False
    write_report(root, report)
    assert (root / "evaluation" / "relatorio_por_produto.json").exists()


def _row(product: str, relative: str, license_name: str, authorized: str) -> dict[str, str]:
    return {
        "produto": product,
        "arquivo": relative,
        "fonte": "teste",
        "url_original": "https://exemplo.invalid/foto.jpg" if authorized == "sim" else "",
        "licenca": license_name,
        "autorizacao_verificada": authorized,
        "sha256": "",
        "grupo_origem": relative,
        "mesmo_original": "nao",
    }


def test_transfer_does_not_download_or_train_when_blocked() -> None:
    with pytest.raises(RuntimeError, match="não autorizado"):
        build_transfer_classifier("resnet18", pretrained=True, authorize_download=False)
    model = build_transfer_classifier("resnet18", num_classes=50, stage="A", pretrained=False)
    frozen = trainable_parameters(model)
    apply_stage(model, "resnet18", "B")
    assert trainable_parameters(model) > frozen
    groups = parameter_groups(model, head_learning_rate=0.001, finetune_learning_rate=0.0001)
    assert groups[0]["lr"] == 0.001
    assert groups[1]["lr"] == 0.0001
    reference = weight_reference("mobilenet_v3_large")
    assert reference["url"]
    assert reference["baixado"] is False
    with pytest.raises(RuntimeError, match="incompleto"):
        assert_ready_for_training({"completo": False}, run_training=True, authorize_download=True)
    with pytest.raises(RuntimeError, match="desabilitado"):
        assert_ready_for_training({"completo": True}, run_training=False, authorize_download=True)


def test_exploratory_split_keeps_origin_groups_together() -> None:
    records = [
        {"arquivo": "a1", "grupo_origem": "mesmo"},
        {"arquivo": "a2", "grupo_origem": "mesmo"},
        {"arquivo": "b", "grupo_origem": "outro"},
        {"arquivo": "c", "grupo_origem": "terceiro"},
    ]
    split = exploratory_group_split(records, seed=42, test_fraction=0.25)
    sides = []
    for row in split["treino"] + split["teste"]:
        if row["grupo_origem"] == "mesmo":
            sides.append("teste" if row in split["teste"] else "treino")
    assert len(set(sides)) == 1
    assert "exploratório" in str(split["limitacao"])
    other = exploratory_group_split(records, seed=42, test_fraction=0.25)
    assert same_protocol(split, other)
    probabilities = np.array([[0.7, 0.2, 0.1], [0.1, 0.2, 0.7]], dtype=float)
    targets = np.array([0, 1])
    assert topk_accuracy(probabilities, targets, 1) == 0.5
    assert topk_accuracy(probabilities, targets, 3) == 1.0
    report = recognition_report(probabilities, targets, [0, 1, 2])
    assert report["top1"] == 0.5
    train_transform = build_brazilian_train_transform()
    eval_transform = build_eval_transform()
    assert len(train_transform.transforms) > len(eval_transform.transforms)


def test_nearest_products_groups_by_identity() -> None:
    from classification.similarity import nearest_products

    vectors = torch.tensor(
        [
            [1.0, 0.0],
            [0.9, 0.1],
            [0.0, 1.0],
        ]
    )
    found = nearest_products(torch.tensor([1.0, 0.0]), vectors, ["BR0001", "BR0001", "BR0002"], ["a", "b", "c"], k=2)
    assert [item["produto"] for item in found] == ["BR0001", "BR0002"]
    assert found[0]["imagem"] == "a"


def test_checkpoint_absence_and_scraping_refusal(tmp_path: Path) -> None:
    assert load_checkpoint(tmp_path / "ausente.pt") is None
    assert top_candidates([0.2, 0.7, 0.1], ["BR0001", "BR0002", "BR0003"])[0]["rotulo"] == "BR0002"
    assert embedding_status(pretrained=True, authorize_download=False) == "download_nao_autorizado"
    assert embedding_status(pretrained=False, authorize_download=False) == "pesos_nao_carregados"
    assert ManualConnector().fetch() == []
    with pytest.raises(RuntimeError, match="não é executado"):
        CommercialScrapingConnector().fetch()
    torch.manual_seed(0)
