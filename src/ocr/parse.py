"""Leitura inicial de valores monetários em fotografias de etiquetas."""

from __future__ import annotations

import re

from pricing.money import MoneyError, format_price, parse_price

_MARKED = re.compile(
    r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2}|\d+\.\d{2})(?!\d)",
    re.IGNORECASE,
)
_BARE = re.compile(
    r"(?<![\d.])(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2})(?!\d)",
)


def find_money_candidates(text: str) -> list[dict[str, str | None]]:
    """Extrai candidatos. A confiança fica nula porque o texto isolado não a traz."""
    found: list[dict[str, str | None]] = []
    occupied: list[tuple[int, int]] = []
    seen: set[tuple[str, str]] = set()
    for pattern in (_MARKED, _BARE):
        for match in pattern.finditer(text):
            if any(match.start() < end and match.end() > start for start, end in occupied):
                continue
            original = match.group(0).strip()
            try:
                value = format_price(parse_price(original))
            except MoneyError:
                continue
            key = (value, original)
            if key in seen:
                continue
            seen.add(key)
            occupied.append((match.start(), match.end()))
            found.append({"valor": value, "texto_original": original, "confianca": None})
    return found
