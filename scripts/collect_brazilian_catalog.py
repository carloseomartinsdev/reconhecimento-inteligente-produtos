"""Coleta o catálogo e as fotos no Open Food Facts.

Só grava imagem cuja licença registrada é CC BY-SA. Não completa quantidade
com cópia, recorte ou figura sintética. Pode ser interrompido e repetido:
os identificadores já gravados em products.json permanecem.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from datasets.off_record import (  # noqa: E402
    DATA_LICENSE,
    IMAGE_LICENSE,
    SOURCE_NAME,
    TERMS_URL,
    image_roles,
    image_url,
    original_image_ids,
    packaging_from_text,
    parse_quantity_text,
    product_url,
    variant_from_name,
)

UA = "ReconhecimentoInteligenteProdutos/2.2 (academic; local POS Disciplina_15)"
COLLECTED_ON = "2026-10-24"
SEARCH = "https://search.openfoodfacts.org/search"
PRODUCT = "https://world.openfoodfacts.org/api/v2/product/{code}.json"
METADATA = ROOT / "data" / "brazilian_products" / "metadata"
IMAGES = ROOT / "data" / "brazilian_products" / "images"
MAX_IMAGES = 5

BUCKETS = (
    {
        "categoria": "Arroz",
        "quota": 6,
        "queries": ['categories_tags:"en:rices" AND countries_tags:"en:brazil"'],
        "require_any": ("arroz",),
        "reject_any": ("biscoito", "bolinho", "snack", "doce", "basmati", "jasmine", "arboreo", "arborio"),
    },
    {
        "categoria": "Feijão",
        "quota": 6,
        "queries": [
            'categories_tags:"en:common-beans" AND countries_tags:"en:brazil"',
            '(product_name:feijao OR product_name:feijão) AND countries_tags:"en:brazil"',
        ],
        "require_any": ("feijao", "feijão"),
        "reject_any": ("enlatado", "tempero", "sopa", "pronto"),
    },
    {
        "categoria": "Açúcar",
        "quota": 4,
        "queries": ['categories_tags:"en:sugars" AND countries_tags:"en:brazil"'],
        "require_any": ("acucar", "açúcar"),
        "reject_any": ("confeitado", "biscoito", "achocolatado", "doce de"),
    },
    {
        "categoria": "Café",
        "quota": 6,
        "queries": ['categories_tags:"en:coffees" AND countries_tags:"en:brazil"'],
        "require_any": ("cafe", "café"),
        "reject_any": ("capsula", "cápsula", "bebida pronta", "achocolatado"),
    },
    {
        "categoria": "Leite UHT",
        "quota": 6,
        "queries": ['categories_tags:"en:uht-milks" AND countries_tags:"en:brazil"'],
        "require_any": ("leite",),
        "reject_any": ("condensado", "po ", "pó", "fermentado", "achocolatado", "creme"),
    },
    {
        "categoria": "Leite em pó",
        "quota": 4,
        "queries": [
            '(product_name:"leite em po" OR product_name:"leite em pó" OR product_name:"milk powder") AND countries_tags:"en:brazil"',
            'product_name:ninho AND countries_tags:"en:brazil"',
        ],
        "require_any": ("po", "pó", "powder"),
        "reject_any": ("condensado", "achocolatado", "composto"),
    },
    {
        "categoria": "Óleo de soja",
        "quota": 4,
        "queries": [
            'categories_tags:"en:soybean-oils" AND countries_tags:"en:brazil"',
            'product_name:soja AND categories_tags:"en:vegetable-oils" AND countries_tags:"en:brazil"',
        ],
        "require_any": ("soja",),
        "reject_any": ("girassol", "canola", "oliva", "milho", "azeite"),
    },
    {
        "categoria": "Farinhas e flocão",
        "quota": 6,
        "queries": [
            'categories_tags:"en:flours" AND countries_tags:"en:brazil"',
            '(product_name:flocao OR product_name:flocão OR product_name:fuba OR product_name:fubá OR product_name:mandioca) AND countries_tags:"en:brazil"',
        ],
        "require_any": ("farinha", "flocao", "flocão", "fuba", "fubá", "mandioca"),
        "reject_any": ("biscoito", "pao ", "pão ", "bolo", "mistura para bolo"),
    },
    {
        "categoria": "Macarrão",
        "quota": 4,
        "queries": ['categories_tags:"en:pastas" AND countries_tags:"en:brazil"'],
        "require_any": ("macarrao", "macarrão", "espaguete", "massa"),
        "reject_any": ("instantaneo", "instantâneo", "sopa", "lasanha pronta", "molho"),
    },
    {
        "categoria": "Sal",
        "quota": 2,
        "queries": ['categories_tags:"en:salts" AND countries_tags:"en:brazil"'],
        "require_any": ("sal",),
        "reject_any": ("salgadinho", "himalaia", "parrilla"),
    },
    {
        "categoria": "Manteiga",
        "quota": 2,
        "queries": ['categories_tags:"en:butters" AND countries_tags:"en:brazil"'],
        "require_any": ("manteiga",),
        "reject_any": ("margarina", "chocolate", "biscoito"),
    },
)


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            if attempt == 3:
                print("falha de consulta", exc, flush=True)
                return {}
            time.sleep(2 + attempt)


def search(query: str, page_size: int = 40) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "q": query,
            "page_size": str(page_size),
            "page": "1",
            "fields": "code,product_name,brands,quantity,categories_tags,countries_tags,completeness",
        }
    )
    payload = fetch_json(f"{SEARCH}?{params}")
    time.sleep(0.4)
    return list(payload.get("hits") or [])


def fold_text(value: str) -> str:
    import unicodedata

    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))


def hit_text(hit: dict) -> str:
    brands = hit.get("brands") or []
    if isinstance(brands, str):
        brands = [brands]
    return fold_text(" ".join([str(hit.get("product_name") or ""), " ".join(brands)]))


def accept_hit(hit: dict, bucket: dict) -> bool:
    name = str(hit.get("product_name") or "").strip()
    brands = hit.get("brands") or []
    if isinstance(brands, str):
        brands = [brands]
    brand = " ".join(brands).strip()
    if not name or not brand or brand.casefold() in {"arroz", "feijao", "feijão", "sal"}:
        return False
    if "en:brazil" not in (hit.get("countries_tags") or []):
        return False
    text = hit_text(hit)
    if not any(fold_text(token) in text for token in bucket["require_any"]):
        return False
    if any(fold_text(token) in text for token in bucket["reject_any"]):
        return False
    return True


def load_product(code: str) -> dict:
    payload = fetch_json(PRODUCT.format(code=code) + "?fields=code,product_name,brands,quantity,packaging,packaging_tags,categories_tags,countries_tags,images,url")
    time.sleep(0.35)
    return payload.get("product") or {}


def build_record(product: dict, category: str) -> dict | None:
    if not product.get("code"):
        return None
    name = str(product.get("product_name") or "").strip()
    raw_brands = str(product.get("brands") or "")
    parts = [part.strip() for part in raw_brands.split(",") if part.strip()]
    folded_name = fold_text(name)
    brand = next((part for part in parts if fold_text(part) in folded_name), raw_brands.strip())
    quantity = parse_quantity_text(str(product.get("quantity") or ""))
    packaging = packaging_from_text(product.get("packaging"), name)
    originals = original_image_ids(product.get("images"))
    if not name or not brand or quantity is None or packaging is None or not originals:
        return None
    if "en:brazil" not in (product.get("countries_tags") or []):
        return None
    variant, variant_evidence = variant_from_name(name)
    amount, unit = quantity
    code = str(product["code"])
    return {
        "codigo_barras": code,
        "nome": name,
        "marca": brand,
        "categoria": category,
        "variante": variant,
        "variante_evidencia": variant_evidence,
        "quantidade": format(amount.normalize(), "f"),
        "unidade": unit,
        "tipo_embalagem": packaging[0],
        "embalagem_evidencia": packaging[1],
        "embalagem_fonte": product.get("packaging"),
        "status_comercial": "validado",
        "fonte": {
            "nome": SOURCE_NAME,
            "url_produto": product.get("url") or product_url(code),
            "codigo_fonte": code,
            "licenca_dados": DATA_LICENSE,
            "licenca_imagens": IMAGE_LICENSE,
            "termos": TERMS_URL,
            "consultado_em": COLLECTED_ON,
        },
        "imagens_originais": originals[:MAX_IMAGES],
        "papeis": image_roles(product.get("images")),
        "tamanhos_fonte": {
            image_id: ((product.get("images") or {}).get(image_id) or {}).get("sizes", {}).get("full")
            for image_id in originals[:MAX_IMAGES]
        },
    }


def assign_ids(records: list[dict], previous: list[dict]) -> list[dict]:
    known = {item["codigo_barras"]: item["id"] for item in previous if item.get("codigo_barras") and item.get("id")}
    used = set(known.values())
    number = 1
    for record in records:
        code = record["codigo_barras"]
        if code in known:
            record["id"] = known[code]
            continue
        while f"BR{number:04d}" in used:
            number += 1
        record["id"] = f"BR{number:04d}"
        used.add(record["id"])
        number += 1
    return records


def download_images(records: list[dict]) -> tuple[list[dict], list[dict]]:
    accepted: list[dict] = []
    rejected: list[dict] = []
    for record in records:
        folder = IMAGES / record["id"]
        folder.mkdir(parents=True, exist_ok=True)
        for image_id in record["imagens_originais"]:
            url = image_url(record["codigo_barras"], image_id)
            destination = folder / f"{image_id}.jpg"
            try:
                request = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(request, timeout=60) as response:
                    content = response.read()
                if not content:
                    raise ValueError("resposta vazia")
                destination.write_bytes(content)
            except Exception as exc:
                rejected.append(
                    {
                        "produto": record["id"],
                        "url_original": url,
                        "motivo": "download_falhou",
                        "detalhe": str(exc),
                    }
                )
                continue
            digest = hashlib.sha256(content).hexdigest()
            full = record["tamanhos_fonte"].get(image_id) or {}
            accepted.append(
                {
                    "produto": record["id"],
                    "arquivo": destination.relative_to(ROOT / "data" / "brazilian_products").as_posix(),
                    "fonte": SOURCE_NAME,
                    "url_original": url,
                    "url_produto": record["fonte"]["url_produto"],
                    "licenca": IMAGE_LICENSE,
                    "autorizacao_verificada": "sim",
                    "autorizacao_url": TERMS_URL,
                    "data_coleta": COLLECTED_ON,
                    "sha256": digest,
                    "resolucao_arquivo": "",
                    "resolucao_original_fonte": f"{full.get('w', '')}x{full.get('h', '')}" if full else "",
                    "formato": "jpeg",
                    "status_validacao": "coletada",
                    "grupo_origem": f"{record['codigo_barras']}:{image_id}",
                    "mesmo_original": "nao",
                    "papel": record["papeis"].get(image_id, "nao_indicado"),
                    "observacao_direitos": "A licença cobre a fotografia do contribuidor. A embalagem pode ter direitos de terceiros.",
                }
            )
            time.sleep(0.15)
    return accepted, rejected


def fill_resolution(rows: list[dict]) -> None:
    from PIL import Image

    for row in rows:
        path = ROOT / "data" / "brazilian_products" / row["arquivo"]
        try:
            with Image.open(path) as image:
                row["resolucao_arquivo"] = f"{image.size[0]}x{image.size[1]}"
                row["formato"] = (image.format or "jpeg").lower()
        except Exception:
            row["status_validacao"] = "arquivo_ilegivel"


def main() -> None:
    METADATA.mkdir(parents=True, exist_ok=True)
    previous_path = METADATA / "products.json"
    previous = []
    if previous_path.exists():
        previous = json.loads(previous_path.read_text(encoding="utf-8")).get("produtos", [])
    selected: list[dict] = []
    seen_codes: set[str] = set()
    seen_identity: set[tuple] = set()
    gaps: list[dict] = []
    for bucket in BUCKETS:
        chosen = 0
        attempts = 0
        hits: list[dict] = []
        for query in bucket["queries"]:
            hits.extend(search(query))
        unique_hits = []
        local_seen: set[str] = set()
        for hit in hits:
            code = str(hit.get("code") or "")
            if code and code not in local_seen:
                local_seen.add(code)
                unique_hits.append(hit)
        unique_hits.sort(key=lambda item: item.get("completeness") or 0, reverse=True)
        for hit in unique_hits:
            if chosen >= bucket["quota"] or attempts >= bucket["quota"] * 8:
                break
            code = str(hit.get("code") or "")
            if code in seen_codes or not accept_hit(hit, bucket):
                continue
            attempts += 1
            product = load_product(code)
            record = build_record(product, bucket["categoria"])
            if record is None:
                continue
            identity = (
                record["marca"].casefold(),
                record["nome"].casefold(),
                record["variante"].casefold(),
                record["quantidade"],
                record["unidade"],
                record["tipo_embalagem"].casefold(),
            )
            if identity in seen_identity:
                continue
            seen_codes.add(code)
            seen_identity.add(identity)
            selected.append(record)
            chosen += 1
            print(bucket["categoria"], chosen, code, record["nome"], flush=True)
        if chosen < bucket["quota"]:
            gaps.append({"categoria": bucket["categoria"], "pedido": bucket["quota"], "validado": chosen})
    assign_ids(selected, previous)
    rows, rejected = download_images(selected)
    fill_resolution(rows)
    public_products = []
    for record in selected:
        item = {key: value for key, value in record.items() if key not in {"imagens_originais", "papeis", "tamanhos_fonte"}}
        item["ativo"] = True
        public_products.append(item)
    payload = {
        "fonte": SOURCE_NAME,
        "consultado_em": COLLECTED_ON,
        "licenca_imagens": IMAGE_LICENSE,
        "licenca_dados": DATA_LICENSE,
        "termos": TERMS_URL,
        "cotas_nao_preenchidas": gaps,
        "produtos": public_products,
    }
    previous_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = METADATA / "image_manifest.csv"
    fieldnames = [
        "produto", "arquivo", "fonte", "url_original", "url_produto", "licenca",
        "autorizacao_verificada", "autorizacao_url", "data_coleta", "sha256",
        "resolucao_arquivo", "resolucao_original_fonte", "formato", "status_validacao",
        "grupo_origem", "mesmo_original", "papel", "observacao_direitos",
    ]
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    (METADATA / "sources.json").write_text(
        json.dumps(
            {
                "fontes": [
                    {
                        "nome": SOURCE_NAME,
                        "termos": TERMS_URL,
                        "licenca_imagens": IMAGE_LICENSE,
                        "licenca_dados": DATA_LICENSE,
                        "atribuicao": "Link para a página do produto e menção da licença CC BY-SA.",
                        "limite": "A licença da fotografia não elimina direitos de marca e de arte da embalagem.",
                        "coleta_executada": True,
                        "scraping_comercial": False,
                    }
                ]
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (METADATA / "imagens_rejeitadas.json").write_text(
        json.dumps(rejected, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("produtos", len(public_products), "imagens", len(rows), "rejeitadas", len(rejected), "lacunas", gaps)


if __name__ == "__main__":
    main()
