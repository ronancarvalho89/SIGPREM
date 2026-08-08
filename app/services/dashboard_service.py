"""
Service de Dashboard — indicadores gerenciais (COMMIT 0039).

Não lança HTTPException.
Centraliza consolidações a partir dos Services existentes.
"""

from decimal import Decimal
from typing import Any

from app.models.venda import Venda
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.movimento_financeiro_repository import (
    MovimentoFinanceiroRepository,
)
from app.repositories.venda_repository import VendaRepository
from app.services.movimento_financeiro_service import MovimentoFinanceiroService
from app.services.venda_service import VendaService


class DashboardService:
    """Centraliza indicadores gerenciais do ERP."""

    def __init__(self, repository: DashboardRepository) -> None:
        """Inicializa o service e os services dependentes."""
        self.repository = repository
        self.financeiro_service = MovimentoFinanceiroService(
            MovimentoFinanceiroRepository(repository.db)
        )
        self.venda_service = VendaService(
            VendaRepository(repository.db)
        )

    def dashboard(self) -> dict[str, Any]:
        """
        Consolida os indicadores gerenciais do dashboard.

        Retorna fluxo financeiro e indicadores comerciais.
        """
        return {
            "fluxo_financeiro": self.financeiro_service.fluxo_caixa(),
            "comercial": self._indicadores_comerciais(),
        }

    def obter_indicadores(self) -> dict[str, int]:
        """Monta os indicadores de contagem já existentes."""
        return {
            "clientes": self.repository.contar_clientes_ativos(),
            "fornecedores": self.repository.contar_fornecedores_ativos(),
            "funcionarios": self.repository.contar_funcionarios_ativos(),
            "produtos": self.repository.contar_produtos_ativos(),
            "producoes": self.repository.contar_producoes(),
            "compras_concreto": self.repository.contar_compras_concreto(),
        }

    def _indicadores_comerciais(self) -> dict[str, Any]:
        """Consolida indicadores comerciais a partir do VendaService."""
        vendas = self._listar_todas_vendas()
        quantidade_vendas = len(vendas)

        if quantidade_vendas == 0:
            zero = Decimal("0")
            return {
                "quantidade_vendas": 0,
                "valor_total_vendas": zero,
                "ticket_medio": zero,
                "maior_venda": zero,
                "menor_venda": zero,
            }

        valores = [Decimal(str(venda.valor_total)) for venda in vendas]
        valor_total_vendas = sum(valores, Decimal("0"))
        ticket_medio = valor_total_vendas / Decimal(quantidade_vendas)

        return {
            "quantidade_vendas": quantidade_vendas,
            "valor_total_vendas": valor_total_vendas,
            "ticket_medio": ticket_medio,
            "maior_venda": max(valores),
            "menor_venda": min(valores),
        }

    def _listar_todas_vendas(self) -> list[Venda]:
        """Lista todas as vendas ativas via VendaService (paginado)."""
        vendas: list[Venda] = []
        skip = 0
        limit = 100

        while True:
            lote = self.venda_service.listar(skip=skip, limit=limit)
            if not lote:
                break

            vendas.extend(lote)

            if len(lote) < limit:
                break

            skip += limit

        return vendas
