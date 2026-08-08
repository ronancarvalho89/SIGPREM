"""
Service de Dashboard — montagem de indicadores (COMMIT 0009).

Não lança HTTPException.
"""

from app.repositories.dashboard_repository import DashboardRepository


class DashboardService:
    """Regras de apresentação dos indicadores do dashboard."""

    def __init__(self, repository: DashboardRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository

    def obter_indicadores(self) -> dict[str, int]:
        """Monta o objeto único com todos os indicadores."""
        return {
            "clientes": self.repository.contar_clientes_ativos(),
            "fornecedores": self.repository.contar_fornecedores_ativos(),
            "funcionarios": self.repository.contar_funcionarios_ativos(),
            "produtos": self.repository.contar_produtos_ativos(),
            "producoes": self.repository.contar_producoes(),
            "compras_concreto": self.repository.contar_compras_concreto(),
        }
