"""Aumento só do conjunto de treino.

Imagens geradas aqui não entram no manifesto como fotografias independentes.
"""

from __future__ import annotations

from torchvision import transforms

from preprocessing.transforms import IMAGENET_MEAN, IMAGENET_STD


def build_brazilian_train_transform(image_size: int = 224) -> transforms.Compose:
    return transforms.Compose(
        [
            transforms.Resize(int(image_size * 1.10)),
            transforms.RandomRotation(degrees=12),
            transforms.ColorJitter(brightness=0.15, contrast=0.15),
            transforms.RandomAffine(degrees=0, translate=(0.04, 0.04), scale=(0.92, 1.08)),
            transforms.CenterCrop(image_size),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )
