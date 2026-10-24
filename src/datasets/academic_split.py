"""Registros utilizáveis e divisão do experimento acadêmico.

A foto de demonstração não entra aqui. Imagens aumentadas também não:
o aumento ocorre só no laço de treino.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

EXCLUDED_ROLES = {"nutrition", "ingredients"}
SPLIT_ID = "academico-grupos-s42"


def load_experiment_records(root: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Devolve registros utilizáveis e os excluídos, sem apagar arquivos."""
    metadata = root / "metadata"
    products = json.loads((metadata / "products.json").read_text(encoding="utf-8"))["produtos"]
    category_by_id = {item["id"]: item["categoria"] for item in products}
    kept: list[dict[str, str]] = []
    excluded: list[dict[str, str]] = []
    with (metadata / "image_manifest.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            reason = _exclusion_reason(root, row, category_by_id)
            record = {
                "produto": row["produto"],
                "arquivo": row["arquivo"],
                "categoria": category_by_id.get(row["produto"], ""),
                "grupo_origem": row.get("grupo_origem") or row["arquivo"],
                "papel": row.get("papel", ""),
                "resolucao": row.get("resolucao_arquivo", ""),
            }
            if reason:
                excluded.append({**record, "motivo": reason})
            else:
                kept.append(record)
    return kept, excluded


def _exclusion_reason(root: Path, row: dict[str, str], category_by_id: dict[str, str]) -> str:
    if row["produto"] not in category_by_id:
        return "produto_ausente_no_catalogo"
    if row.get("papel") in EXCLUDED_ROLES:
        return "verso_ou_tabela_nao_e_frente_da_embalagem"
    path = root / row["arquivo"]
    if not path.exists():
        return "arquivo_ausente"
    try:
        with Image.open(path) as image:
            image.verify()
    except (UnidentifiedImageError, OSError):
        return "arquivo_corrompido"
    return ""


def academic_group_split(
    records: list[dict[str, str]],
    *,
    seed: int = 42,
) -> dict[str, object]:
    """70/15/15 por categoria, com cada grupo de origem em um único conjunto.

    Categorias com menos de três grupos independentes não preenchem os três
    conjuntos. Essa limitação fica registrada; nenhum grupo é copiado.
    """
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for record in records:
        grouped[record["grupo_origem"]].append(record)
    by_category: dict[str, list[str]] = defaultdict(list)
    for group_id, members in grouped.items():
        by_category[members[0]["categoria"]].append(group_id)

    rng = np.random.default_rng(seed)
    assignment: dict[str, str] = {}
    limitations: list[str] = []
    for category, group_ids in sorted(by_category.items()):
        order = [group_ids[int(index)] for index in rng.permutation(len(group_ids))]
        train_ids, val_ids, test_ids = _allocate(order)
        if not val_ids or not test_ids:
            limitations.append(
                f"{category}: {len(order)} grupo(s) de origem. "
                "Não há amostra independente para todos os conjuntos."
            )
        for group_id in train_ids:
            assignment[group_id] = "treino"
        for group_id in val_ids:
            assignment[group_id] = "validacao"
        for group_id in test_ids:
            assignment[group_id] = "teste"

    buckets: dict[str, list[dict[str, str]]] = {"treino": [], "validacao": [], "teste": []}
    for group_id, members in grouped.items():
        buckets[assignment[group_id]].extend(members)
    return {
        "split_id": f"academico-grupos-s{seed}",
        "seed": seed,
        "estrategia": (
            "Grupos de origem permanecem inteiros. Dentro de cada categoria, "
            "cerca de 70% vai ao treino, 15% à validação e 15% ao teste, "
            "com ao menos um grupo em cada conjunto quando existem três ou mais."
        ),
        "limitacoes": limitations,
        "treino": buckets["treino"],
        "validacao": buckets["validacao"],
        "teste": buckets["teste"],
    }


def _allocate(group_ids: list[str]) -> tuple[list[str], list[str], list[str]]:
    count = len(group_ids)
    if count >= 3:
        test_count = max(1, int(round(count * 0.15)))
        val_count = max(1, int(round(count * 0.15)))
        while test_count + val_count >= count:
            if test_count > val_count:
                test_count -= 1
            else:
                val_count -= 1
        return (
            group_ids[test_count + val_count :],
            group_ids[test_count : test_count + val_count],
            group_ids[:test_count],
        )
    if count == 2:
        return group_ids[:1], group_ids[1:], []
    return group_ids, [], []


def assert_no_group_leakage(split: dict[str, object]) -> None:
    seen: dict[str, str] = {}
    for name in ("treino", "validacao", "teste"):
        for record in split[name]:
            group_id = str(record["grupo_origem"])
            previous = seen.get(group_id)
            if previous is not None and previous != name:
                raise ValueError(f"O grupo {group_id} aparece em {previous} e {name}.")
            seen[group_id] = name


def category_counts(records: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for record in records:
        counts[record["categoria"]] += 1
    return dict(sorted(counts.items()))
