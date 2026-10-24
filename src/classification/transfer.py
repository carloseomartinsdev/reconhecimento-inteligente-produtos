"""Transfer learning para as 50 classes brasileiras.

O download dos pesos ImageNet e o treino ficam bloqueados até haver autorização
e um relatório de dataset marcado como completo. Este módulo não baixa arquivo
ao ser importado.
"""

from __future__ import annotations

from typing import Literal

import torch.nn as nn
from torchvision.models import MobileNet_V3_Large_Weights, ResNet18_Weights

from classification.models import ArchitectureName, build_classifier

Stage = Literal["A", "B"]


def weight_reference(architecture: ArchitectureName) -> dict[str, object]:
    weights = MobileNet_V3_Large_Weights.DEFAULT if architecture == "mobilenet_v3_large" else ResNet18_Weights.DEFAULT
    meta = dict(weights.meta)
    return {
        "arquitetura": architecture,
        "nome": weights.name if hasattr(weights, "name") else str(weights),
        "url": weights.url,
        "meta": meta,
        "baixado": False,
    }


def apply_stage(model: nn.Module, architecture: ArchitectureName, stage: Stage) -> nn.Module:
    for parameter in model.parameters():
        parameter.requires_grad = False
    if architecture == "mobilenet_v3_large":
        for parameter in model.classifier.parameters():
            parameter.requires_grad = True
        if stage == "B":
            blocks = list(model.features.children())[-3:]
            for block in blocks:
                for parameter in block.parameters():
                    parameter.requires_grad = True
        return model
    for parameter in model.fc.parameters():
        parameter.requires_grad = True
    if stage == "B":
        for parameter in model.layer4.parameters():
            parameter.requires_grad = True
    return model


def build_transfer_classifier(
    architecture: ArchitectureName,
    num_classes: int = 50,
    stage: Stage = "A",
    *,
    pretrained: bool = False,
    authorize_download: bool = False,
) -> nn.Module:
    if pretrained and not authorize_download:
        raise RuntimeError(
            "Download dos pesos ImageNet não autorizado. "
            "A fase 2.2 registra a origem e não baixa o arquivo sem autorização explícita."
        )
    model = build_classifier(architecture, num_classes, pretrained=pretrained)
    return apply_stage(model, architecture, stage)


def parameter_groups(
    model: nn.Module,
    *,
    head_learning_rate: float,
    finetune_learning_rate: float,
) -> list[dict[str, object]]:
    head_names = ("classifier", "fc")
    head = []
    backbone = []
    for name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            continue
        if name.startswith(head_names):
            head.append(parameter)
        else:
            backbone.append(parameter)
    groups: list[dict[str, object]] = [{"params": head, "lr": head_learning_rate}]
    if backbone:
        groups.append({"params": backbone, "lr": finetune_learning_rate})
    return groups


def assert_ready_for_training(report: dict[str, object], *, run_training: bool, authorize_download: bool) -> None:
    if not run_training:
        raise RuntimeError("Treinamento desabilitado em experiments.run_training.")
    if not report.get("completo"):
        raise RuntimeError("Dataset incompleto. O treinamento não foi iniciado.")
    if not authorize_download:
        raise RuntimeError("Download dos pesos ImageNet não autorizado.")
