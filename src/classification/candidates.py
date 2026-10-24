"""Candidatos de um checkpoint real.

Sem arquivo de pesos treinado, a função não devolve classe.
"""

from __future__ import annotations

from pathlib import Path

import torch


def top_candidates(probabilities: list[float], labels: list[str], k: int = 3) -> list[dict[str, object]]:
    if len(probabilities) != len(labels):
        raise ValueError("Probabilidades e rótulos têm tamanhos diferentes.")
    if not labels:
        return []
    order = sorted(range(len(labels)), key=lambda index: probabilities[index], reverse=True)
    return [
        {"rotulo": labels[index], "probabilidade": float(probabilities[index]), "posicao": position + 1}
        for position, index in enumerate(order[:k])
    ]


def load_checkpoint(path: Path) -> dict | None:
    if not path.exists():
        return None
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(payload, dict) or "state_dict" not in payload or "labels" not in payload:
        raise ValueError("O checkpoint não tem state_dict e labels.")
    return payload
