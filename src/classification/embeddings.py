"""Embeddings do extrator, no mesmo protocolo da classificação.

Sem o arquivo de pesos autorizado, o vetor não é um embedding ImageNet.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from classification.models import ArchitectureName


def embedding_status(*, pretrained: bool, authorize_download: bool) -> str:
    if pretrained and not authorize_download:
        return "download_nao_autorizado"
    if not pretrained:
        return "pesos_nao_carregados"
    return "pesos_autorizados"


def embed_batch(model: nn.Module, architecture: ArchitectureName, batch: torch.Tensor) -> torch.Tensor:
    """Usa o extrator já construído. Não carrega peso nenhum."""
    model.eval()
    with torch.no_grad():
        if architecture == "mobilenet_v3_large":
            features = model.features(batch)
            pooled = model.avgpool(features)
            return torch.flatten(pooled, 1)
        features = model.conv1(batch)
        features = model.bn1(features)
        features = model.relu(features)
        features = model.maxpool(features)
        features = model.layer1(features)
        features = model.layer2(features)
        features = model.layer3(features)
        features = model.layer4(features)
        features = model.avgpool(features)
        return torch.flatten(features, 1)
