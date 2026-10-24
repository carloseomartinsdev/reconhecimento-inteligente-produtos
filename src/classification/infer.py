"""Inferência de classificação, separada do treino."""

from __future__ import annotations

import torch
import torch.nn as nn


def predict_proba(model: nn.Module, batch: torch.Tensor, device: torch.device) -> torch.Tensor:
    model.eval()
    with torch.no_grad():
        logits = model(batch.to(device))
        return torch.softmax(logits, dim=1)
