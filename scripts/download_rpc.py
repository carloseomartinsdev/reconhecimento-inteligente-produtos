"""Consulta das fontes do RPC e download somente com confirmação explícita.

Uso informativo, que é o padrão:

    python scripts/download_rpc.py --check

O download do pacote de aproximadamente 16 GB só é tentado com as duas
flags abaixo e com o cliente oficial do Kaggle já autenticado:

    python scripts/download_rpc.py --confirm-download --i-accept-cc-by-nc-sa-4
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "data" / "public" / "downloads"
DATASET = "diyer22/retail-product-checkout-dataset"
PROJECT_PAGE = "https://rpc-dataset.github.io/"
KAGGLE_PAGE = "https://www.kaggle.com/datasets/diyer22/retail-product-checkout-dataset"
LICENSE_NAME = "CC BY-NC-SA 4.0"


def build_report() -> str:
    return "\n".join(
        [
            "RPC — Retail Product Checkout",
            f"Página oficial: {PROJECT_PAGE}",
            f"Kaggle: {KAGGLE_PAGE}",
            f"Licença declarada na página oficial: {LICENSE_NAME}",
            "Tamanho informado: cerca de 15 GB na página oficial e 15,91 GB no explorador do Kaggle.",
            "Conteúdo esperado após extração:",
            "  data/public/rpc/train2019/",
            "  data/public/rpc/val2019/",
            "  data/public/rpc/test2019/",
            "  data/public/rpc/instances_train2019.json",
            "  data/public/rpc/instances_val2019.json",
            "  data/public/rpc/instances_test2019.json",
            "Alternativa citada pela página oficial: Baidu Drive, cujo link deve ser copiado da própria página.",
            "Uso acadêmico não comercial é a condição da licença. O dataset não entra no controle de versão.",
            "Download não iniciado.",
        ]
    )


def attempt_download() -> int:
    executable = shutil.which("kaggle")
    if executable is None:
        print(
            "O comando kaggle não está disponível. Instale e autentique o cliente oficial antes de repetir.",
            file=sys.stderr,
        )
        return 3
    DESTINATION.mkdir(parents=True, exist_ok=True)
    command = [
        executable,
        "datasets",
        "download",
        "-d",
        DATASET,
        "-p",
        str(DESTINATION),
        "--unzip",
    ]
    print("Iniciando download confirmado pelo usuário.")
    completed = subprocess.run(command, check=False)
    return int(completed.returncode)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepara o download do RPC sem executá-lo por padrão.")
    parser.add_argument("--check", action="store_true", help="Mostra fonte, licença, tamanho e layout esperado.")
    parser.add_argument("--confirm-download", action="store_true")
    parser.add_argument("--i-accept-cc-by-nc-sa-4", action="store_true")
    args = parser.parse_args(argv)
    print(build_report())
    if not args.confirm_download:
        print("Para baixar depois da autorização, use --confirm-download --i-accept-cc-by-nc-sa-4.")
        return 0
    if not args.i_accept_cc_by_nc_sa_4:
        print("Download recusado: a licença CC BY-NC-SA 4.0 não foi aceita explicitamente.", file=sys.stderr)
        return 2
    return attempt_download()


if __name__ == "__main__":
    raise SystemExit(main())
