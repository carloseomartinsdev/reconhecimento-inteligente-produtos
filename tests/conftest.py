"""Testes da fase 1. Nenhum caso depende do dataset RPC completo."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture
def project_root() -> Path:
    return ROOT
