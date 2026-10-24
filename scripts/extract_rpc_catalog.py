"""Gera ou confere o catálogo preliminar e, se houver JSON, extrai o oficial.

    python scripts/extract_rpc_catalog.py
    python scripts/extract_rpc_catalog.py --json data/public/rpc/instances_val2019.json
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from datasets.catalog import load_rpc_catalog  # noqa: E402
from datasets.rpc_preliminary import iter_preliminary_classes  # noqa: E402
from evaluation.annotations import categories_from_coco, load_json  # noqa: E402
from utils.config import load_config, resolve_path  # noqa: E402

CATALOG_FIELDS = [
    "category_id",
    "name",
    "supercategory",
    "supercategory_pt",
    "chinese_name",
    "sku_name",
    "source",
    "verification_status",
]


def write_preliminary(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = iter_preliminary_classes()
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CATALOG_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Catálogo preliminar gravado: {path} ({len(rows)} classes).")


def diff_against_preliminary(official_rows: list[dict[str, object]], preliminary_path: Path) -> list[str]:
    preliminary = load_rpc_catalog(preliminary_path)
    current = {int(row.category_id): (row.name, row.supercategory) for row in preliminary.itertuples(index=False)}
    messages = []
    for row in official_rows:
        category_id = int(row["category_id"])
        observed = (str(row["name"]), str(row["supercategory"]))
        expected = current.get(category_id)
        if expected is None:
            messages.append(f"id {category_id} existe no JSON e não está no catálogo preliminar.")
        elif expected != observed:
            messages.append(
                f"id {category_id}: preliminar {expected[0]}/{expected[1]} ; JSON {observed[0]}/{observed[1]}"
            )
    official_ids = {int(row["category_id"]) for row in official_rows}
    for category_id in sorted(set(current) - official_ids):
        messages.append(f"id {category_id} está no catálogo preliminar e não veio no JSON.")
    return messages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Escreve o catálogo preliminar ou compara com um JSON local.")
    parser.add_argument("--json", type=Path, default=None, help="instances_*.json já baixado.")
    parser.add_argument("--write-preliminary", action="store_true")
    args = parser.parse_args(argv)
    config = load_config("default.yaml")
    catalog_path = resolve_path(config["paths"]["catalog_rpc"])
    if args.write_preliminary or not catalog_path.is_file():
        write_preliminary(catalog_path)
    else:
        frame = load_rpc_catalog(catalog_path)
        print(f"Catálogo existente: {catalog_path} ({len(frame)} classes).")
    if args.json is None:
        print("JSON oficial ausente nesta execução. Nenhuma classe foi confirmada localmente.")
        return 0
    if not args.json.is_file():
        print(f"JSON não encontrado: {args.json}", file=sys.stderr)
        return 2
    payload = load_json(args.json)
    official_rows = categories_from_coco(payload)
    messages = diff_against_preliminary(official_rows, catalog_path)
    print(f"Categorias lidas do JSON: {len(official_rows)}.")
    if not messages:
        print("Os nomes e supercategorias do JSON coincidem com o catálogo preliminar.")
        return 0
    print("Diferenças encontradas:")
    for message in messages:
        print(f"- {message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
