"""Números publicados do RPC e conferência com arquivos locais.

Os valores numéricos deste módulo foram transcritos da página oficial do
dataset em 24 de outubro de 2026. Eles descrevem a publicação, não uma
contagem feita sobre arquivos desta máquina.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_PAGE = "https://rpc-dataset.github.io/"
KAGGLE_PAGE = "https://www.kaggle.com/datasets/diyer22/retail-product-checkout-dataset"
PAPER_ARXIV = "https://arxiv.org/abs/1901.07249"
PAPER_DOI = "https://doi.org/10.1007/s11432-022-3513-y"
LICENSE = "CC BY-NC-SA 4.0"

# Página oficial, seção 3.2, consultada em 2026-10-24.
PUBLISHED_SPLITS = {
    "train": {
        "role": "exemplar",
        "images": 53739,
        "objects": 53739,
        "objects_per_image": 1.0,
        "categories_per_image": 1.0,
    },
    "val": {
        "role": "checkout",
        "images": 6000,
        "objects": 73602,
        "objects_per_image": 12.27,
        "categories_per_image": 6.33,
    },
    "test": {
        "role": "checkout",
        "images": 24000,
        "objects": 294333,
        "objects_per_image": 12.26,
        "categories_per_image": 6.31,
    },
}

# Página oficial, seção 3.5. Os 30.000 checkout images reúnem validação e teste.
PUBLISHED_CLUTTER = {
    "easy": {"images": 10000, "objects": 71496, "objects_per_image": 7.15, "categories_per_image": 3.81},
    "medium": {"images": 10000, "objects": 122961, "objects_per_image": 12.30, "categories_per_image": 6.27},
    "hard": {"images": 10000, "objects": 173478, "objects_per_image": 17.35, "categories_per_image": 8.87},
}

# Artigo arXiv:1901.07249, seção 3.2.2.
CAPTURE = {
    "exemplar_resolution": (2592, 1944),
    "checkout_resolution": (1800, 1800),
    "exemplar_cameras": 4,
    "turntable_step_degrees": 9,
    "views_per_side": 160,
    "checkout_board_cm": (80, 80),
    "sku_count": 200,
    "meta_category_count": 17,
    "total_images": 83739,
    "checkout_images": 30000,
    "checkout_objects": 367935,
}

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def published_totals() -> dict[str, int]:
    images = sum(item["images"] for item in PUBLISHED_SPLITS.values())
    checkout_objects = PUBLISHED_SPLITS["val"]["objects"] + PUBLISHED_SPLITS["test"]["objects"]
    clutter_images = sum(item["images"] for item in PUBLISHED_CLUTTER.values())
    clutter_objects = sum(item["objects"] for item in PUBLISHED_CLUTTER.values())
    return {
        "images": images,
        "checkout_objects_from_splits": checkout_objects,
        "clutter_images": clutter_images,
        "clutter_objects": clutter_objects,
    }


def inspect_local_rpc(root: Path) -> dict[str, object]:
    """Conta arquivos locais se o dataset tiver sido colocado em root.

    A ausência dos arquivos é um estado esperado na fase 1.
    """
    root = Path(root)
    expected_dirs = ("train2019", "val2019", "test2019")
    expected_json = (
        "instances_train2019.json",
        "instances_val2019.json",
        "instances_test2019.json",
    )
    directories = {}
    for name in expected_dirs:
        path = root / name
        if not path.is_dir():
            directories[name] = {"present": False, "image_files": 0}
            continue
        count = sum(
            1
            for file in path.rglob("*")
            if file.is_file() and file.suffix.lower() in IMAGE_SUFFIXES
        )
        directories[name] = {"present": True, "image_files": count}
    annotations = {
        name: (root / name).is_file()
        for name in expected_json
    }
    present_parts = sum(1 for item in directories.values() if item["present"]) + sum(annotations.values())
    return {
        "root": str(root),
        "root_exists": root.is_dir(),
        "status": "absent" if present_parts == 0 else "partial_or_present",
        "directories": directories,
        "annotations": annotations,
        "local_image_files": sum(item["image_files"] for item in directories.values()),
        "published_images": CAPTURE["total_images"],
        "note": (
            "Contagem local de arquivos de imagem. "
            "Ela só pode ser comparada aos números publicados depois do download."
        ),
    }
