"""Conectores de atualização de preços.

Nenhum conector desta fase consulta um site comercial.
"""

from __future__ import annotations

from typing import Protocol


class PriceConnector(Protocol):
    name: str

    def describe(self) -> dict[str, object]:
        """Descreve a fonte e se a coleta automática está autorizada."""

    def fetch(self) -> list[dict[str, object]]:
        """Retorna observações já autorizadas. Não é chamado para scraping."""


class ManualConnector:
    name = "manual"

    def describe(self) -> dict[str, object]:
        return {
            "nome": self.name,
            "executa_rede": False,
            "campos": [
                "produto",
                "estabelecimento",
                "valor",
                "regiao",
                "data_observacao",
                "fonte",
                "condicoes_comerciais",
                "status_validacao",
            ],
        }

    def fetch(self) -> list[dict[str, object]]:
        return []


class AuthorizedSourceConnector:
    """Reservado para uma fonte que publique permissão de coleta automática."""

    name = "fonte_autorizada"

    def __init__(self, authorized: bool = False) -> None:
        self.authorized = authorized

    def describe(self) -> dict[str, object]:
        return {
            "nome": self.name,
            "autorizada": self.authorized,
            "executa_rede": False,
            "prioridade": "Usar somente fonte que autorize coleta automatizada.",
        }

    def fetch(self) -> list[dict[str, object]]:
        if not self.authorized:
            raise RuntimeError("Não há fonte automática autorizada nesta fase.")
        return []


class CommercialScrapingConnector:
    name = "scraping_comercial"

    def describe(self) -> dict[str, object]:
        return {
            "nome": self.name,
            "executa_rede": False,
            "estado": "nao_executado",
            "motivo": "A fase 2.2 não coleta preços em sites comerciais.",
        }

    def fetch(self) -> list[dict[str, object]]:
        raise RuntimeError("Scraping comercial não é executado nesta fase.")
