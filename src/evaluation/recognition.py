"""Métricas e divisão exploratória.

Uma divisão com quatro ou cinco fotos por classe não sustenta desempenho
generalizável. O retorno inclui essa limitação.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np

from evaluation.classification import classification_scores


EXPLORATORY_LIMITATION = (
    "A divisão preserva grupos de origem, mas as fotos públicas não repetem "
    "um protocolo de captura. O número resultante é exploratório."
)


def topk_accuracy(probabilities: np.ndarray, targets: np.ndarray, k: int) -> float:
    if probabilities.ndim != 2:
        raise ValueError("probabilities precisa ter forma (n, classes).")
    if len(targets) != len(probabilities):
        raise ValueError("probabilities e targets têm tamanhos diferentes.")
    if len(targets) == 0:
        raise ValueError("Não há exemplos.")
    k = min(k, probabilities.shape[1])
    order = np.argsort(-probabilities, axis=1)[:, :k]
    hits = (order == targets.reshape(-1, 1)).any(axis=1)
    return float(hits.mean())


def recognition_report(probabilities: np.ndarray, targets: np.ndarray, labels: list[int]) -> dict[str, object]:
    predicted = probabilities.argmax(axis=1)
    scores = classification_scores(targets.tolist(), predicted.tolist(), labels)
    return {
        "top1": topk_accuracy(probabilities, targets, 1),
        "top3": topk_accuracy(probabilities, targets, 3),
        "top5": topk_accuracy(probabilities, targets, 5),
        "classificacao": scores,
        "limitacao": EXPLORATORY_LIMITATION,
    }


def exploratory_group_split(
    records: list[dict[str, str]],
    *,
    seed: int = 42,
    test_fraction: float = 0.25,
) -> dict[str, object]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for record in records:
        group = record.get("grupo_origem") or record["arquivo"]
        grouped[group].append(record)
    groups = sorted(grouped)
    rng = np.random.default_rng(seed)
    order = list(rng.permutation(len(groups)))
    test_groups = max(1, int(round(len(groups) * test_fraction))) if groups else 0
    test_ids = {groups[index] for index in order[:test_groups]}
    train, test = [], []
    for group, rows in grouped.items():
        (test if group in test_ids else train).extend(rows)
    return {
        "split_id": f"exploratorio-grupos-s{seed}",
        "treino": train,
        "teste": test,
        "grupos_teste": sorted(test_ids),
        "limitacao": EXPLORATORY_LIMITATION,
        "fotografias_independentes": False,
    }


def same_protocol(left: dict[str, object], right: dict[str, object]) -> bool:
    return left.get("split_id") == right.get("split_id") and left.get("teste") == right.get("teste")
