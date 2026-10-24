"""Inspeciona o diretório local do RPC e valida imagens ou anotações apontadas.

    python scripts/inspect_rpc.py
    python scripts/validate_data.py --images pasta --coco anotacao.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from datasets.rpc_reference import inspect_local_rpc  # noqa: E402
from evaluation.annotations import load_json, validate_coco, validate_yolo_label_text  # noqa: E402
from preprocessing.validate import validate_image  # noqa: E402
from utils.config import load_config, resolve_path  # noqa: E402


def inspect() -> int:
    config = load_config("default.yaml")
    root = resolve_path(config["paths"]["rpc_root"])
    report = inspect_local_rpc(root)
    print(f"status: {report['status']}")
    print(f"raiz: {report['root']}")
    print(f"imagens locais: {report['local_image_files']}")
    print(f"imagens publicadas: {report['published_images']}")
    for name, info in report["directories"].items():
        print(f"  {name}: presente={info['present']} arquivos={info['image_files']}")
    for name, present in report["annotations"].items():
        print(f"  {name}: presente={present}")
    return 0


def validate(images: Path | None, coco: Path | None, yolo: Path | None) -> int:
    error_count = 0
    if images is not None:
        files = [path for path in images.rglob("*") if path.is_file()]
        print(f"Imagens encontradas: {len(files)}")
        for file_path in files:
            issues = validate_image(file_path)
            for issue in issues:
                print(f"{issue['level']}\t{file_path.name}\t{issue['code']}\t{issue['message']}")
                if issue["level"] == "error":
                    error_count += 1
    if coco is not None:
        issues = validate_coco(load_json(coco), image_root=images)
        for issue in issues:
            print(f"{issue['level']}\tcoco\t{issue['code']}\t{issue['message']}")
            if issue["level"] == "error":
                error_count += 1
        if not issues:
            print("COCO: nenhuma inconsistência encontrada.")
    if yolo is not None:
        issues = validate_yolo_label_text(yolo.read_text(encoding="utf-8"))
        for issue in issues:
            print(f"{issue['level']}\tyolo\t{issue['code']}\t{issue['message']}")
            if issue["level"] == "error":
                error_count += 1
        if not issues:
            print("YOLO: nenhuma inconsistência encontrada.")
    return 1 if error_count else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspeciona o RPC local ou valida arquivos informados.")
    parser.add_argument("--images", type=Path, default=None)
    parser.add_argument("--coco", type=Path, default=None)
    parser.add_argument("--yolo", type=Path, default=None)
    args = parser.parse_args(argv)
    if args.images is None and args.coco is None and args.yolo is None:
        return inspect()
    return validate(args.images, args.coco, args.yolo)


if __name__ == "__main__":
    raise SystemExit(main())
