"""Catálogo preliminar das 200 categorias do RPC.

Os nomes foram lidos do cartão de categorias do espelho Hugging Face
``benjamintli/retail-product-checkout`` em 24 de outubro de 2026.
Eles repetem o padrão ``{id}_{supercategory}`` descrito por quem inspecionou
``instances_val2019.json``. Este módulo não substitui essa conferência:
``scripts/extract_rpc_catalog.py`` regrava o catálogo quando o JSON oficial
estiver disponível.

Bebidas e bebidas alcoólicas não formam blocos contíguos nessa lista.
O SKU 21 aparece como fruta seca. As duas observações precisam ser
confirmadas no JSON oficial antes de qualquer conclusão sobre a taxonomia.
"""

from __future__ import annotations

from collections import Counter

PRELIMINARY_SOURCE = (
    "huggingface:benjamintli/retail-product-checkout class_label names; "
    "README accessed 2026-10-24"
)
VERIFICATION_STATUS = "preliminary_pending_official_json"

# Intervalos inclusivos (category_id inicial, category_id final, supercategory).
PRELIMINARY_RANGES: tuple[tuple[int, int, str], ...] = (
    (1, 12, "puffed_food"),
    (13, 21, "dried_fruit"),
    (22, 30, "dried_food"),
    (31, 41, "instant_drink"),
    (42, 53, "instant_noodles"),
    (54, 70, "dessert"),
    (71, 78, "drink"),
    (79, 80, "alcohol"),
    (81, 87, "drink"),
    (88, 96, "alcohol"),
    (97, 107, "milk"),
    (108, 121, "canned_food"),
    (122, 133, "chocolate"),
    (134, 141, "gum"),
    (142, 151, "candy"),
    (152, 163, "seasoner"),
    (164, 173, "personal_hygiene"),
    (174, 193, "tissue"),
    (194, 200, "stationery"),
)

META_CATEGORY_PT = {
    "puffed_food": "alimento inflado",
    "dried_fruit": "fruta seca",
    "dried_food": "alimento desidratado",
    "instant_drink": "bebida instantânea",
    "instant_noodles": "macarrão instantâneo",
    "dessert": "sobremesa",
    "drink": "bebida",
    "alcohol": "bebida alcoólica",
    "milk": "leite",
    "canned_food": "enlatado",
    "chocolate": "chocolate",
    "gum": "goma de mascar",
    "candy": "bala",
    "seasoner": "tempero",
    "personal_hygiene": "higiene pessoal",
    "tissue": "lenço de papel",
    "stationery": "papelaria",
}


def iter_preliminary_classes() -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    for start, end, supercategory in PRELIMINARY_RANGES:
        for category_id in range(start, end + 1):
            rows.append(
                {
                    "category_id": category_id,
                    "name": f"{category_id}_{supercategory}",
                    "supercategory": supercategory,
                    "supercategory_pt": META_CATEGORY_PT[supercategory],
                    "chinese_name": "",
                    "sku_name": "",
                    "source": PRELIMINARY_SOURCE,
                    "verification_status": VERIFICATION_STATUS,
                }
            )
    return rows


def supercategory_counts() -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in iter_preliminary_classes():
        counts[str(row["supercategory"])] += 1
    return dict(sorted(counts.items()))
