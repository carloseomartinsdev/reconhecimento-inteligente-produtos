"""Fábricas do Modelo A (MobileNetV3-Large) e do Modelo B (ResNet18).

``pretrained=False`` evita o download dos pesos ImageNet. A fase experimental
poderá ligar a inicialização ImageNet de forma explícita.
"""

from __future__ import annotations

from typing import Literal

import torch.nn as nn
from torchvision.models import (
    MobileNet_V3_Large_Weights,
    ResNet18_Weights,
    mobilenet_v3_large,
    resnet18,
)

ArchitectureName = Literal["mobilenet_v3_large", "resnet18"]


def build_classifier(
    architecture: ArchitectureName,
    num_classes: int,
    pretrained: bool = False,
) -> nn.Module:
    if num_classes < 2:
        raise ValueError("num_classes deve ser pelo menos 2.")
    if architecture == "mobilenet_v3_large":
        weights = MobileNet_V3_Large_Weights.DEFAULT if pretrained else None
        model = mobilenet_v3_large(weights=weights)
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, num_classes)
        return model
    if architecture == "resnet18":
        weights = ResNet18_Weights.DEFAULT if pretrained else None
        model = resnet18(weights=weights)
        in_features = model.fc.in_features
        model.fc = nn.Linear(in_features, num_classes)
        return model
    raise ValueError(f"Arquitetura não suportada: {architecture}")


def count_parameters(module: nn.Module) -> int:
    return sum(parameter.numel() for parameter in module.parameters())


def trainable_parameters(module: nn.Module) -> int:
    return sum(parameter.numel() for parameter in module.parameters() if parameter.requires_grad)
