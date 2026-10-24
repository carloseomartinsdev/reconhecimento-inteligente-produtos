"""Medidas de custo computacional, separadas das métricas de acerto."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

import torch.nn as nn


def measure_latency(function: Callable[[], object], warmup: int = 1, repeats: int = 5) -> dict[str, float]:
    if warmup < 0 or repeats < 1:
        raise ValueError("warmup precisa ser não negativo e repeats pelo menos 1.")
    for _ in range(warmup):
        function()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        function()
        samples.append(time.perf_counter() - start)
    return {
        "repeats": float(repeats),
        "mean_seconds": sum(samples) / len(samples),
        "min_seconds": min(samples),
        "max_seconds": max(samples),
    }


def parameter_bytes(module: nn.Module) -> int:
    total = 0
    for parameter in module.parameters():
        total += parameter.numel() * parameter.element_size()
    return total


def file_size_bytes(path: Path) -> int | None:
    file_path = Path(path)
    if not file_path.is_file():
        return None
    return file_path.stat().st_size
