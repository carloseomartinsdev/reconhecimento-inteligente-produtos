"""Métricas de classificação.

As funções calculam os vetores recebidos. Um teste unitário que passa
rótulos sintéticos não é um resultado do dataset.
"""

from __future__ import annotations

from typing import Sequence

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)


def classification_scores(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    labels: Sequence[int] | None = None,
) -> dict[str, object]:
    if len(y_true) == 0:
        raise ValueError("y_true está vazio.")
    if len(y_true) != len(y_pred):
        raise ValueError("y_true e y_pred têm tamanhos diferentes.")
    label_list = list(labels) if labels is not None else sorted(set(y_true) | set(y_pred))
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=label_list,
        average=None,
        zero_division=0,
    )
    precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=label_list,
        average="macro",
        zero_division=0,
    )
    matrix = confusion_matrix(y_true, y_pred, labels=label_list)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(precision_macro),
        "recall_macro": float(recall_macro),
        "f1_macro": float(f1_macro),
        "labels": label_list,
        "precision_per_class": [float(value) for value in precision],
        "recall_per_class": [float(value) for value in recall],
        "f1_per_class": [float(value) for value in f1],
        "support_per_class": [int(value) for value in support],
        "confusion_matrix": matrix.tolist(),
    }
