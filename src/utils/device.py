"""Seleção de CPU ou GPU sem assumir que a GPU existe."""

from __future__ import annotations

import torch


def get_device(prefer_gpu: bool = True) -> torch.device:
    if prefer_gpu and torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def device_description(device: torch.device | None = None) -> dict[str, str | bool | int | None]:
    selected = device if device is not None else get_device(True)
    cuda_available = torch.cuda.is_available()
    name = None
    if cuda_available:
        name = torch.cuda.get_device_name(0)
    return {
        "selected": str(selected),
        "cuda_available": cuda_available,
        "cuda_device_count": int(torch.cuda.device_count()),
        "cuda_device_name": name,
        "torch_version": torch.__version__,
    }
