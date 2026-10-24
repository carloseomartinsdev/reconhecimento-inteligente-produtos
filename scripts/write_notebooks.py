"""Gera os notebooks preparatórios da fase 1. Não executa treino."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks"

BOOTSTRAP = """from pathlib import Path
import sys

ROOT = Path.cwd().resolve()
while not (ROOT / "pyproject.toml").exists() and ROOT != ROOT.parent:
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))
print(f"Raiz do projeto: {ROOT}")
"""

NOTEBOOKS = {
    "01_exploracao_dataset.ipynb": [
        (
            "md",
            """# 01 — Exploração do dataset

Este notebook prepara a leitura do RPC e do catálogo preliminar.

Não baixa o dataset e não treina modelo. As contagens de 83.739 imagens vêm da página oficial; a célula de inventário mostra quantos arquivos existem nesta máquina.
""",
        ),
        ("code", BOOTSTRAP),
        (
            "code",
            """from datasets.catalog import load_rpc_catalog, summarize_catalog
from datasets.rpc_reference import CAPTURE, PUBLISHED_CLUTTER, PUBLISHED_SPLITS, inspect_local_rpc, published_totals
from utils.config import load_config, resolve_path

config = load_config("default.yaml")
catalog = load_rpc_catalog(resolve_path(config["paths"]["catalog_rpc"]))
summary = summarize_catalog(catalog)
inventory = inspect_local_rpc(resolve_path(config["paths"]["rpc_root"]))

print("Classes no catálogo preliminar:", summary["n_categories"])
print("Metacategorias:", summary["n_supercategories"])
print("Situação:", summary["verification_status"])
print("Imagens publicadas:", CAPTURE["total_images"])
print("Totais conferidos pela transcrição:", published_totals())
print("Inventário local:", inventory["status"], "arquivos", inventory["local_image_files"])
print("Partições publicadas:", {name: item["images"] for name, item in PUBLISHED_SPLITS.items()})
print("Densidades publicadas:", {name: item["images"] for name, item in PUBLISHED_CLUTTER.items()})
""",
        ),
        (
            "md",
            """## Quando os arquivos locais existirem

A próxima fase deve calcular, a partir do JSON, imagens por SKU, objetos por imagem, densidade quando o nome ou o campo permitir, e a diferença entre este catálogo e `categories`. Essas contagens substituem o inventário local, hoje em zero. Elas não substituem a citação da página oficial enquanto o pacote não for lido.
""",
        ),
    ],
    "02_analise_preprocessamento.ipynb": [
        (
            "md",
            """# 02 — Análise de pré-processamento

Os presets do E2 estão implementados e ainda não foram comparados em acurácia.

- `baseline_imagenet` e `identity_scale` redimensionam para quadrado e alteram a proporção.
- `letterbox` preserva a proporção.
- `equalize` e `clahe` atuam na luminância antes do redimensionamento.

A célula constrói uma imagem sintética. Ela não estima qualidade de reconhecimento.
""",
        ),
        ("code", BOOTSTRAP),
        (
            "code",
            """import numpy as np
from preprocessing.ops import apply_preset

image = np.zeros((60, 120, 3), dtype=np.uint8)
image[:, :40] = (20, 20, 20)
image[:, 40:80] = (180, 180, 180)
image[:, 80:] = (80, 40, 40)

for preset in ("baseline_imagenet", "letterbox", "clahe", "equalize", "identity_scale"):
    output = apply_preset(image, preset, size=64)
    print(f"{preset:20} shape={output.shape} dtype={output.dtype}")
""",
        ),
        (
            "md",
            """## Leitura prevista no E2

Com a partição P-CLS-exemplar congelada, uma única arquitetura será treinada em cada preset. O F1 macro da validação é a métrica de comparação. Esta célula não dispara esse treino.
""",
        ),
        (
            "code",
            """RUN_EXPERIMENT = False
if RUN_EXPERIMENT:
    raise RuntimeError("O E2 ainda não está liberado.")
print("Experimento E2 não executado.")
""",
        ),
    ],
    "03_classificacao_mobilenet.ipynb": [
        (
            "md",
            """# 03 — Classificação com MobileNetV3-Large

Modelo A. A cabeça final é substituída pelo número de classes do experimento. `pretrained=False` evita o download dos pesos ImageNet durante esta preparação.

O protocolo de treino é o P-CLS-exemplar, descrito em `docs/04_metodologia.md`.
""",
        ),
        ("code", BOOTSTRAP),
        (
            "code",
            """import torch
from classification.infer import predict_proba
from classification.models import build_classifier, count_parameters
from utils.device import get_device
from utils.seed import set_seed

set_seed(42)
device = get_device(prefer_gpu=True)
model = build_classifier("mobilenet_v3_large", num_classes=8, pretrained=False).to(device)
model.eval()
batch = torch.zeros(1, 3, 224, 224, device=device)
probabilities = predict_proba(model, batch, device)
print("Dispositivo:", device)
print("Parâmetros:", count_parameters(model))
print("Saída:", tuple(probabilities.shape))
print("Soma das probabilidades:", float(probabilities.sum()))
""",
        ),
        (
            "code",
            """from classification.train import train_classifier

RUN_TRAINING = False
if RUN_TRAINING:
    train_classifier(enabled=True)
else:
    print("Treino do MobileNetV3 não executado.")
""",
        ),
    ],
    "04_classificacao_resnet.ipynb": [
        (
            "md",
            """# 04 — Classificação com ResNet18

Modelo B, no mesmo protocolo e com a mesma semente do Modelo A. A diferença preparada aqui é apenas a arquitetura e o número de parâmetros. A comparação de acurácia pertence ao E1.
""",
        ),
        ("code", BOOTSTRAP),
        (
            "code",
            """import torch
from classification.infer import predict_proba
from classification.models import build_classifier, count_parameters
from utils.device import get_device
from utils.seed import set_seed

set_seed(42)
device = get_device(prefer_gpu=True)
model = build_classifier("resnet18", num_classes=8, pretrained=False).to(device)
probabilities = predict_proba(model, torch.zeros(1, 3, 224, 224, device=device), device)
print("Dispositivo:", device)
print("Parâmetros:", count_parameters(model))
print("Saída:", tuple(probabilities.shape))
""",
        ),
        (
            "code",
            """from classification.train import train_classifier

RUN_TRAINING = False
if RUN_TRAINING:
    train_classifier(enabled=True)
else:
    print("Treino do ResNet18 não executado.")
""",
        ),
    ],
    "05_deteccao_yolo.ipynb": [
        (
            "md",
            """# 05 — Detecção com YOLO

Modelo C, variante planejada `yolo11n`, pela implementação Ultralytics. O notebook não baixa pesos. A carga só ocorre se um arquivo local for informado e existir.

O E3 usa cenas de checkout. Treinar só com exemplares é um ensaio de domínio à parte, não o número principal.
""",
        ),
        ("code", BOOTSTRAP),
        (
            "code",
            """from pathlib import Path
from detection.yolo import load_local_yolo, train_detector, yolo_plan
from utils.config import load_config

config = load_config("default.yaml", "detection.yaml")
print(yolo_plan(
    architecture=config["detection"]["architecture"],
    weights=config["detection"]["weights"],
))

weights = Path("models") / "yolo11n.pt"
try:
    load_local_yolo(weights)
except FileNotFoundError as exc:
    print(exc)
""",
        ),
        (
            "code",
            """RUN_TRAINING = False
if RUN_TRAINING:
    train_detector(enabled=True)
else:
    print("Treino do YOLO não executado.")
""",
        ),
    ],
    "06_reconhecimento_hibrido.ipynb": [
        (
            "md",
            """# 06 — Reconhecimento híbrido

Modelo D. O detector propõe a caixa; a CNN classifica o recorte; a confiança combinada é o produto dos dois escores. A margem está em `configs/hybrid.yaml`.

A célula usa uma imagem sintética para verificar o recorte. Não há detecção real.
""",
        ),
        ("code", BOOTSTRAP),
        (
            "code",
            """import numpy as np
from hybrid.pipeline import crop_hwc, fuse_scores
from utils.config import load_config

config = load_config("hybrid.yaml")
margin = config["hybrid"]["crop_margin"]
image = np.zeros((200, 240, 3), dtype=np.uint8)
image[40:120, 50:150] = (0, 180, 30)
crop = crop_hwc(image, (50, 40, 150, 120), margin=margin)
print("Margem:", margin)
print("Recorte:", crop.shape)
print("Fusão 0,80 x 0,70 =", fuse_scores(0.80, 0.70))
""",
        ),
        (
            "code",
            """from hybrid.pipeline import train_hybrid

RUN_TRAINING = False
if RUN_TRAINING:
    train_hybrid(enabled=True)
else:
    print("Treino híbrido não executado.")
""",
        ),
    ],
    "07_avaliacao_comparativa.ipynb": [
        (
            "md",
            """# 07 — Avaliação comparativa

As funções abaixo calculam os vetores que recebem. O exemplo é um fixture de teste, com quatro rótulos e uma caixa, para mostrar a forma do relatório. Não é resultado de produto comercial.

A comparação justa dos experimentos está em `docs/06_experimentos.md`.
""",
        ),
        ("code", BOOTSTRAP),
        (
            "code",
            """from evaluation.classification import classification_scores
from evaluation.detection import average_precision

print("Fixture de classificação")
print(classification_scores([0, 0, 1, 1], [0, 1, 1, 1], labels=[0, 1]))

ground_truth = [{"image_id": "img", "box": (0, 0, 10, 10)}]
prediction = [{"image_id": "img", "score": 0.9, "box": (0, 0, 10, 10)}]
print("AP do fixture de detecção:", average_precision(prediction, ground_truth))
print("Nenhum arquivo em results/metrics foi produzido por esta célula.")
""",
        ),
    ],
    "08_robustez_generalizacao.ipynb": [
        (
            "md",
            """# 08 — Robustez e generalização

O E5 estratifica as fotos próprias por ângulo, distância, iluminação, fundo e densidade. O E6 só cruza RPC e dataset próprio quando `class_mapping.csv` registra correspondência `exact` ou `visual_similar`.

A célula mostra o estado atual do mapeamento e um exemplo de vazamento de grupo de captura.
""",
        ),
        ("code", BOOTSTRAP),
        (
            "code",
            """import pandas as pd
from datasets.catalog import correspondence_status, load_class_mapping
from datasets.manifest import leakage_report
from utils.config import load_config, resolve_path

config = load_config("default.yaml")
mapping = load_class_mapping(resolve_path(config["paths"]["class_mapping"]))
print(correspondence_status(mapping))

frame = pd.DataFrame(
    [
        {
            "image_id": "a",
            "relative_path": "a.jpg",
            "sha256": "h1",
            "parent_image_id": "",
            "capture_group": "produto_frontal",
            "session_id": "20261024_0900_lab",
            "split": "train",
        },
        {
            "image_id": "b",
            "relative_path": "b.jpg",
            "sha256": "h2",
            "parent_image_id": "",
            "capture_group": "produto_frontal",
            "session_id": "20261024_0900_lab",
            "split": "test",
        },
    ]
)
report = leakage_report(frame)
print("Vazamentos de grupo:", report["leakage_count"])
for finding in report["findings"]:
    print(finding)
""",
        ),
    ],
}


def cell(kind: str, source: str) -> dict:
    lines = source.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    if kind == "md":
        return {"cell_type": "markdown", "metadata": {}, "source": lines}
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": lines,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, cells in NOTEBOOKS.items():
        notebook = {
            "nbformat": 4,
            "nbformat_minor": 5,
            "metadata": {
                "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                "language_info": {"name": "python", "pygments_lexer": "ipython3"},
            },
            "cells": [cell(kind, source) for kind, source in cells],
        }
        path = OUT / name
        path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
        print(path.name)


if __name__ == "__main__":
    main()
