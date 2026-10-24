"""Modelo C: YOLO via Ultralytics.

Instanciar ``YOLO('yolo11n.pt')`` dispara download. Este módulo só abre um
arquivo de pesos que já exista localmente.
"""

from __future__ import annotations

from pathlib import Path


def yolo_plan(architecture: str = "yolo11n", weights: str | None = None) -> dict[str, str | None]:
    return {
        "framework": "ultralytics",
        "architecture": architecture,
        "weights": weights,
        "download": "disabled_in_phase_1",
    }


def load_local_yolo(weights_path: Path):
    path = Path(weights_path)
    if not path.is_file():
        raise FileNotFoundError(
            f"Pesos YOLO não encontrados em {path}. "
            "O download automático de pesos não faz parte da fase 1."
        )
    from ultralytics import YOLO

    return YOLO(str(path))


def train_detector(*args: object, enabled: bool = False, **kwargs: object) -> None:
    del args, kwargs
    if not enabled:
        raise RuntimeError(
            "Treinamento do detector desabilitado na fase 1. "
            "Nenhum peso YOLO será baixado ou ajustado."
        )
    raise NotImplementedError("O treino YOLO será implementado na fase experimental.")
