"""Proximidade visual com o extrator ImageNet.

O resultado ordena embalagens do catálogo. Não é a saída de um classificador
treinado nesses produtos.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import torch
import torch.nn.functional as functional
from PIL import Image

from classification.embeddings import embed_batch
from classification.models import build_classifier
from preprocessing.transforms import build_eval_transform

ARCHITECTURE = "mobilenet_v3_large"
SKIPPED_ROLES = {"nutrition", "ingredients"}


def load_encoder() -> torch.nn.Module:
    """Carrega o MobileNetV3-Large com os pesos ImageNet do torchvision."""
    model = build_classifier(ARCHITECTURE, num_classes=2, pretrained=True)
    model.eval()
    return model


def nearest_products(
    query: torch.Tensor,
    vectors: torch.Tensor,
    product_ids: list[str],
    paths: list[str],
    k: int = 3,
) -> list[dict[str, object]]:
    if query.ndim == 2:
        query = query.squeeze(0)
    scores = torch.matmul(vectors, query)
    best: dict[str, dict[str, object]] = {}
    for score, product_id, path in zip(scores.tolist(), product_ids, paths, strict=True):
        current = best.get(product_id)
        if current is None or score > float(current["similaridade"]):
            best[product_id] = {
                "produto": product_id,
                "similaridade": float(score),
                "imagem": path,
            }
    ordered = sorted(best.values(), key=lambda item: float(item["similaridade"]), reverse=True)
    return ordered[:k]


def reference_rows(manifest_path: Path) -> list[dict[str, str]]:
    with manifest_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    by_product: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_product.setdefault(row["produto"], []).append(row)
    chosen: list[dict[str, str]] = []
    for group in by_product.values():
        preferred = [row for row in group if row.get("papel") not in SKIPPED_ROLES]
        chosen.extend(preferred or group)
    return chosen


def _embed_file(model: torch.nn.Module, path: Path, transform) -> torch.Tensor:
    with Image.open(path) as image:
        batch = transform(image.convert("RGB")).unsqueeze(0)
    vector = embed_batch(model, ARCHITECTURE, batch)
    return functional.normalize(vector, dim=1).squeeze(0).cpu()


def embed_file(model: torch.nn.Module, path: Path) -> torch.Tensor:
    return _embed_file(model, path, build_eval_transform())


def load_or_build_index(
    model: torch.nn.Module,
    dataset_root: Path,
    cache_path: Path,
) -> dict[str, object]:
    manifest = dataset_root / "metadata" / "image_manifest.csv"
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    if cache_path.exists():
        cached = torch.load(cache_path, map_location="cpu", weights_only=False)
        if cached.get("manifest_sha256") == digest:
            return cached
    rows = reference_rows(manifest)
    product_ids: list[str] = []
    paths: list[str] = []
    vectors = []
    transform = build_eval_transform()
    for row in rows:
        relative = row["arquivo"]
        path = dataset_root / relative
        if not path.exists():
            continue
        product_ids.append(row["produto"])
        paths.append(relative)
        vectors.append(_embed_file(model, path, transform))
    if not vectors:
        raise FileNotFoundError("Não há imagem de referência para comparar.")
    payload = {
        "manifest_sha256": digest,
        "product_ids": product_ids,
        "paths": paths,
        "vectors": torch.stack(vectors),
        "metodo": "MobileNetV3-Large ImageNet, similaridade de cosseno",
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, cache_path)
    return payload
