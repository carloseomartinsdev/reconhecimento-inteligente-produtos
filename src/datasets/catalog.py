"""Leitura do catálogo de classes e do mapeamento entre origens."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_CATALOG_COLUMNS = (
    "category_id",
    "name",
    "supercategory",
    "supercategory_pt",
    "chinese_name",
    "sku_name",
    "source",
    "verification_status",
)

MAPPING_COLUMNS = (
    "custom_class_id",
    "custom_class_name",
    "rpc_category_id",
    "rpc_category_name",
    "match_type",
    "evidence",
    "notes",
)

USABLE_MATCHES = {"exact", "visual_similar"}


def load_rpc_catalog(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = [column for column in REQUIRED_CATALOG_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Catálogo sem colunas obrigatórias: {missing}")
    frame["category_id"] = frame["category_id"].astype(int)
    duplicated = frame["category_id"].duplicated().any()
    if duplicated:
        raise ValueError("Catálogo contém category_id repetido.")
    return frame.sort_values("category_id").reset_index(drop=True)


def summarize_catalog(frame: pd.DataFrame) -> dict[str, object]:
    counts = (
        frame.groupby("supercategory")
        .size()
        .sort_index()
        .astype(int)
        .to_dict()
    )
    return {
        "n_categories": int(frame["category_id"].nunique()),
        "n_supercategories": int(frame["supercategory"].nunique()),
        "per_supercategory": counts,
        "sources": sorted(frame["source"].unique().tolist()),
        "verification_status": sorted(frame["verification_status"].unique().tolist()),
        "chinese_names_filled": int((frame["chinese_name"].str.len() > 0).sum()),
    }


def load_class_mapping(path: Path) -> pd.DataFrame:
    if not path.is_file():
        return pd.DataFrame(columns=list(MAPPING_COLUMNS))
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = [column for column in MAPPING_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Mapeamento sem colunas obrigatórias: {missing}")
    return frame


def correspondence_status(frame: pd.DataFrame) -> dict[str, object]:
    """Decide se E6 pode cruzar origens.

    Sem linhas utilizáveis, a decisão metodológica é manter experimentos
    separados. Isso evita forçar uma correspondência que o catálogo não sustenta.
    """
    if frame.empty:
        return {
            "status": "unmapped",
            "n_rows": 0,
            "n_usable_matches": 0,
            "experiment": "separate",
        }
    usable = frame[frame["match_type"].isin(USABLE_MATCHES)]
    if usable.empty:
        return {
            "status": "no_correspondence",
            "n_rows": int(len(frame)),
            "n_usable_matches": 0,
            "experiment": "separate",
        }
    return {
        "status": "correspondence_recorded",
        "n_rows": int(len(frame)),
        "n_usable_matches": int(len(usable)),
        "experiment": "cross_evaluation_possible",
    }
