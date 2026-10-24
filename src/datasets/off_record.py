"""Leitura dos campos publicados pelo Open Food Facts.

Nenhum nome, marca, quantidade ou embalagem é preenchido fora do texto da fonte.
"""

from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation

SOURCE_NAME = "Open Food Facts"
TERMS_URL = "https://world.openfoodfacts.org/terms-of-use"
IMAGE_LICENSE = "CC BY-SA"
DATA_LICENSE = "ODbL e DbCL"
ALLOWED_IMAGE_LICENSES = {IMAGE_LICENSE}

_VARIANT_TOKENS = (
    "torrado e moído",
    "torrado e moido",
    "extra forte",
    "extraforte",
    "semi desnatado",
    "semidesnatado",
    "zero lactose",
    "com ovos",
    "sem sal",
    "com sal",
    "parboilizado",
    "tradicional",
    "integral",
    "agulhinha",
    "carioca",
    "fradinho",
    "demerara",
    "mascavo",
    "cristal",
    "refinado",
    "solúvel",
    "soluvel",
    "desnatado",
    "flocão",
    "flocao",
    "mandioca",
    "espaguete",
    "parafuso",
    "penne",
    "sêmola",
    "semola",
    "iodado",
    "tipo 1",
    "tipo 2",
    "preto",
    "branco",
    "trigo",
    "milho",
    "grosso",
)

_PACKAGING_TOKENS = (
    ("sache", "Sachê"),
    ("sachê", "Sachê"),
    ("vácuo", "Vácuo"),
    ("vacuo", "Vácuo"),
    ("garrafa", "Garrafa"),
    ("pacote", "Pacote"),
    ("caixa", "Caixa"),
    ("vidro", "Vidro"),
    ("lata", "Lata"),
    ("pote", "Pote"),
    ("papel", "Papel"),
    ("plástico", "Plástico"),
    ("plastico", "Plástico"),
)

_QUANTITY = re.compile(
    r"(?P<number>\d+(?:[.,]\d+)?)\s*(?P<unit>kg|g|ml|l|lt|litro|litros|un|und|unidade|unidades)\b",
    re.IGNORECASE,
)


def fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))


def product_url(code: str) -> str:
    return f"https://world.openfoodfacts.org/product/{code}"


def barcode_path(code: str) -> str:
    if len(code) <= 8:
        return code
    return "/".join((code[0:3], code[3:6], code[6:9], code[9:]))


def image_url(code: str, image_id: str, size: str | None = None) -> str:
    suffix = ".jpg" if not size else f".{size}.jpg"
    return f"https://images.openfoodfacts.org/images/products/{barcode_path(code)}/{image_id}{suffix}"


def parse_quantity_text(quantity: str | None) -> tuple[Decimal, str] | None:
    if not quantity:
        return None
    matches = list(_QUANTITY.finditer(quantity))
    if len(matches) != 1:
        return None
    match = matches[0]
    try:
        number = Decimal(match.group("number").replace(",", "."))
    except InvalidOperation:
        return None
    if number <= 0:
        return None
    unit_key = fold(match.group("unit"))
    if unit_key in {"l", "lt", "litro", "litros"}:
        unit = "L"
    elif unit_key in {"un", "und", "unidade", "unidades"}:
        unit = "un"
    elif unit_key in {"kg", "g", "ml"}:
        unit = unit_key
    else:
        return None
    return number, unit


def longest_token(text: str, tokens: tuple[str, ...]) -> str | None:
    folded = fold(text)
    found = [token for token in tokens if fold(token) in folded]
    if not found:
        return None
    return max(found, key=lambda token: len(fold(token)))


def variant_from_name(name: str) -> tuple[str, str | None]:
    token = longest_token(name, _VARIANT_TOKENS)
    if token is None:
        return "", None
    return token, "trecho_do_nome_na_fonte"


def packaging_from_text(*texts: str | None) -> tuple[str, str] | None:
    for label, text in (("campo_packaging", texts[0] if texts else None), ("nome_na_fonte", texts[1] if len(texts) > 1 else None)):
        if not text:
            continue
        folded = fold(text)
        for needle, canonical in _PACKAGING_TOKENS:
            if fold(needle) in folded:
                return canonical, label
    return None


def original_image_ids(images: dict | None) -> list[str]:
    if not images:
        return []
    return sorted((key for key in images if str(key).isdigit()), key=int)


def image_roles(images: dict | None) -> dict[str, str]:
    """Associa o id original ao papel publicado, quando a fonte indica esse papel."""
    roles: dict[str, str] = {}
    if not images:
        return roles
    for key, payload in images.items():
        if not isinstance(payload, dict):
            continue
        image_id = str(payload.get("imgid") or "")
        if not image_id.isdigit():
            continue
        role = str(key).split("_", 1)[0]
        if role in {"front", "ingredients", "nutrition", "packaging"} and image_id not in roles:
            roles[image_id] = role
    return roles
