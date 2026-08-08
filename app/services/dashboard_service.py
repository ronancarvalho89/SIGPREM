"""
Service de Dashboard — indicadores gerenciais (COMMIT 0038).

Não lança HTTPException.
Centraliza consolidações a partir dos Services existentes.
"""

from typing import Any

from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.movimento_financeiro_repository import (
    MovimentoFinanceiroRepository,
)
from app.services.movimento_financeiro_service import MovimentoFinanceiroService


class DashboardService:
    """Centraliza indicadores gerenciais do ERP."""

    def __init__(self, repository: DashboardRepository) -> None:
        """Inicializa o service e os services dependentes."""
        self.repository = repository
        self.financeiro_service = MovimentoFinanceiroService(
            MovimentoFinanceiroRepository(repository.db)
        )

    def dashboard(self) -> dict[str, Any]:
        """
        Consolida os indicadores gerenciais do dashboard.

        Neste commit retorna apenas o fluxo financeiro,
        obtido via MovimentoFinanceiroService.fluxo_caixa().
        """
        return {
            "fluxo_financeiro": self.financeiro_service.fluxo_caixa(),
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
