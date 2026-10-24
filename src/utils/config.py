"""Leitura de configuração e caminhos relativos à raiz do projeto."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_MARKERS = ("pyproject.toml", "requirements.txt")


def project_root() -> Path:
    """Raiz do repositório, localizada a partir deste arquivo."""
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if all((candidate / marker).exists() for marker in PROJECT_MARKERS):
            return candidate
    raise FileNotFoundError("Não foi possível localizar a raiz do projeto.")


def resolve_path(relative: str | Path, root: Path | None = None) -> Path:
    path = Path(relative)
    if path.is_absolute():
        return path
    base = root if root is not None else project_root()
    return (base / path).resolve()


def _deep_merge(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in incoming.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(*names: str, root: Path | None = None) -> dict[str, Any]:
    """Carrega um ou mais YAML em configs/ e mescla na ordem recebida."""
    if not names:
        names = ("default.yaml",)
    base = root if root is not None else project_root()
    merged: dict[str, Any] = {}
    for name in names:
        path = base / "configs" / name
        if not path.is_file():
            raise FileNotFoundError(f"Configuração ausente: {path}")
        with path.open(encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
        if not isinstance(loaded, dict):
            raise ValueError(f"A configuração {name} precisa ser um mapeamento.")
        merged = _deep_merge(merged, loaded)
    return merged
