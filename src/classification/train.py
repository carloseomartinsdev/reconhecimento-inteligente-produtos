"""Ponto de entrada do treino. Na fase 1 a chamada é recusada."""

from __future__ import annotations


def assert_training_enabled(enabled: bool) -> None:
    if not enabled:
        raise RuntimeError(
            "Treinamento desabilitado. A fase 1 prepara o protocolo e não ajusta pesos. "
            "experiments.run_training só deve ser verdadeiro na fase experimental."
        )


def train_classifier(*args: object, enabled: bool = False, **kwargs: object) -> None:
    del args, kwargs
    assert_training_enabled(enabled)
    raise NotImplementedError("O laço de treino será implementado na fase experimental.")
