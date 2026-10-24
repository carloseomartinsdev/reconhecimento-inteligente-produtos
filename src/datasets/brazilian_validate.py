"""Validação do dataset brasileiro.

O relatório descreve o que está no disco. Não completa lacunas.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from datasets.off_record import ALLOWED_IMAGE_LICENSES

MIN_SIDE = 224
DUPLICATE_HAMMING = 4
CATEGORY_QUOTAS = {
    "Arroz": 6,
    "Feijão": 6,
    "Açúcar": 4,
    "Café": 6,
    "Leite UHT": 6,
    "Leite em pó": 4,
    "Óleo de soja": 4,
    "Farinhas e flocão": 6,
    "Macarrão": 4,
    "Sal": 2,
    "Manteiga": 2,
}
MINIMUM_IMAGES = 4
TARGET_IMAGES = 5


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def average_hash(path: Path, size: int = 16) -> str | None:
    try:
        with Image.open(path) as image:
            gray = image.convert("L").resize((size, size))
            pixels = list(gray.get_flattened_data() if hasattr(gray, "get_flattened_data") else gray.getdata())
    except (UnidentifiedImageError, OSError):
        return None
    mean = sum(pixels) / len(pixels)
    return "".join("1" if pixel >= mean else "0" for pixel in pixels)


def hamming(left: str, right: str) -> int:
    return sum(bit_left != bit_right for bit_left, bit_right in zip(left, right, strict=True))


def load_products(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    products = payload["produtos"] if isinstance(payload, dict) else payload
    return list(products)


def load_manifest(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _issue(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def validate_dataset(root: Path, *, min_side: int = MIN_SIDE) -> dict[str, object]:
    metadata = root / "metadata"
    products = load_products(metadata / "products.json") if (metadata / "products.json").exists() else []
    manifest = load_manifest(metadata / "image_manifest.csv")
    by_product: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in manifest:
        by_product[row.get("produto", "")].append(row)

    hashes: dict[str, str] = {}
    visual: dict[str, list[tuple[str, str]]] = defaultdict(list)
    image_reports: list[dict[str, object]] = []
    valid_counts: dict[str, int] = defaultdict(int)

    for row in manifest:
        product_id = row.get("produto", "")
        relative = row.get("arquivo", "")
        path = root / relative
        reasons: list[dict[str, str]] = []
        if row.get("licenca") not in ALLOWED_IMAGE_LICENSES:
            reasons.append(_issue("licenca_desconhecida", "A licença não está na lista autorizada."))
        if not row.get("url_original") or not row.get("fonte"):
            reasons.append(_issue("origem_desconhecida", "Fonte ou URL original ausente."))
        if row.get("autorizacao_verificada") != "sim":
            reasons.append(_issue("sem_autorizacao", "A autorização de uso não foi registrada."))
        if not path.exists():
            reasons.append(_issue("arquivo_ausente", "O arquivo do manifesto não está no disco."))
        else:
            try:
                with Image.open(path) as image:
                    image.verify()
                with Image.open(path) as image:
                    width, height = image.size
            except (UnidentifiedImageError, OSError) as exc:
                reasons.append(_issue("arquivo_corrompido", str(exc)))
                width = height = 0
            else:
                if min(width, height) < min_side:
                    reasons.append(_issue("resolucao_insuficiente", f"{width}x{height}"))
                digest = file_sha256(path)
                recorded = row.get("sha256", "")
                if recorded and recorded != digest:
                    reasons.append(_issue("hash_divergente", "O SHA-256 do arquivo difere do manifesto."))
                previous = hashes.get(digest)
                if previous is not None:
                    reasons.append(_issue("duplicata_exata", previous))
                else:
                    hashes[digest] = relative
                visual_hash = average_hash(path)
                if visual_hash is not None and len(set(visual_hash)) > 1:
                    for other_file, other_hash in visual[product_id]:
                        if hamming(visual_hash, other_hash) <= DUPLICATE_HAMMING:
                            reasons.append(_issue("duplicata_visual", other_file))
                            break
                    visual[product_id].append((relative, visual_hash))
        if row.get("mesmo_original") == "sim":
            reasons.append(_issue("derivada_da_mesma_fotografia", row.get("grupo_origem", "")))
        accepted = not reasons
        if accepted:
            valid_counts[product_id] += 1
        image_reports.append({"arquivo": relative, "produto": product_id, "aceita": accepted, "motivos": reasons})

    product_reports = []
    approved_complete = 0
    for product in products:
        product_id = str(product["id"])
        count = valid_counts[product_id]
        commercial_ok = product.get("status_comercial") == "validado"
        image_ok = count >= MINIMUM_IMAGES
        if commercial_ok and image_ok:
            approved_complete += 1
        product_reports.append(
            {
                "id": product_id,
                "categoria": product.get("categoria"),
                "nome": product.get("nome"),
                "status_comercial": product.get("status_comercial"),
                "imagens_no_manifesto": len(by_product.get(product_id, [])),
                "imagens_validas": count,
                "minimo": MINIMUM_IMAGES,
                "atingiu_minimo": image_ok,
                "conteudo_revisado_manualmente": False,
            }
        )

    counts = defaultdict(int)
    for product in products:
        if product.get("status_comercial") == "validado":
            counts[str(product.get("categoria"))] += 1
    quota_ok = all(counts[category] >= quota for category, quota in CATEGORY_QUOTAS.items())
    total_valid = sum(valid_counts.values())
    complete = quota_ok and approved_complete == sum(CATEGORY_QUOTAS.values()) and total_valid >= MINIMUM_IMAGES * 50
    return {
        "completo": complete,
        "produtos_no_catalogo": len(products),
        "produtos_com_minimo_de_imagens": approved_complete,
        "imagens_validas": total_valid,
        "minimo_de_imagens": 200,
        "meta_de_imagens": 250,
        "cotas": {category: {"pedido": quota, "validado": counts[category]} for category, quota in CATEGORY_QUOTAS.items()},
        "produtos": product_reports,
        "imagens": image_reports,
        "limitacao": (
            "A revisão visual de cada embalagem não foi feita imagem por imagem. "
            "O validador confere arquivo, licença, origem, resolução e duplicata."
        ),
    }


def write_report(root: Path, report: dict[str, object]) -> Path:
    destination = root / "evaluation" / "relatorio_por_produto.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return destination
