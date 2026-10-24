"""Esquema dos manifestos e detecção de vazamento entre partições."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

SINGLE_IMAGE_COLUMNS = (
    "image_id",
    "relative_path",
    "origin",
    "class_id",
    "session_id",
    "capture_group",
    "capture_date",
    "angle",
    "distance",
    "lighting",
    "background",
    "split",
    "width",
    "height",
    "sha256",
    "parent_image_id",
    "notes",
)

SCENE_COLUMNS = (
    "scene_id",
    "relative_path",
    "origin",
    "session_id",
    "density",
    "lighting",
    "background",
    "n_objects",
    "split",
    "annotation_path",
    "notes",
)

ALLOWED_ORIGINS = {"public_rpc", "custom"}
ALLOWED_SPLITS = {"train", "val", "test", "unlabeled", "ignored"}
# Uma sessão de coleta pode reunir várias condições independentes.
# O bloqueio padrão usa o grupo de captura, o arquivo e a imagem de origem.
# session_id entra na checagem apenas quando a política de partição é por sessão.
BLOCKING_GROUP_COLUMNS = (
    "image_id",
    "relative_path",
    "sha256",
    "parent_image_id",
    "capture_group",
)


def read_manifest(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def missing_columns(frame: pd.DataFrame, required: tuple[str, ...]) -> list[str]:
    return [column for column in required if column not in frame.columns]


def validate_manifest_values(frame: pd.DataFrame) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if frame.empty:
        issues.append(
            {
                "level": "warning",
                "code": "empty_manifest",
                "message": "O manifesto não tem linhas. Isso é esperado antes da coleta.",
            }
        )
        return issues
    if "origin" in frame.columns:
        unknown = sorted(set(frame["origin"]) - ALLOWED_ORIGINS - {""})
        for value in unknown:
            issues.append(
                {
                    "level": "error",
                    "code": "origin",
                    "message": f"Origem não prevista: {value}",
                }
            )
    if "split" in frame.columns:
        unknown_splits = sorted(set(frame["split"]) - ALLOWED_SPLITS - {""})
        for value in unknown_splits:
            issues.append(
                {
                    "level": "error",
                    "code": "split",
                    "message": f"Partição não prevista: {value}",
                }
            )
    return issues


def find_group_leakage(
    frame: pd.DataFrame,
    group_column: str,
    split_column: str = "split",
) -> list[dict[str, object]]:
    """Aponta um identificador que aparece em mais de uma partição.

    Sessão, grupo de captura, imagem de origem de um recorte, hash e caminho
    devem permanecer em uma única partição.
    """
    if group_column not in frame.columns or split_column not in frame.columns:
        return []
    usable = frame[
        (frame[group_column].astype(str).str.len() > 0)
        & (frame[split_column].astype(str).str.len() > 0)
        & (~frame[split_column].isin(["unlabeled", "ignored"]))
    ]
    leaked: list[dict[str, object]] = []
    for value, part in usable.groupby(group_column):
        splits = sorted(set(part[split_column].astype(str)))
        if len(splits) > 1:
            leaked.append(
                {
                    "group": group_column,
                    "value": str(value),
                    "splits": splits,
                    "count": int(len(part)),
                }
            )
    return leaked


def leakage_report(
    frame: pd.DataFrame,
    extra_group_columns: tuple[str, ...] = (),
) -> dict[str, object]:
    columns = tuple(dict.fromkeys((*BLOCKING_GROUP_COLUMNS, *extra_group_columns)))
    findings = []
    for column in columns:
        findings.extend(find_group_leakage(frame, column))
    return {
        "leakage_count": len(findings),
        "findings": findings,
        "checked_columns": [column for column in columns if column in frame.columns],
    }
