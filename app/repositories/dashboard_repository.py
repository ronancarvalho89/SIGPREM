"""
Repository de Dashboard — consultas agregadas (COMMIT 0009).

Responsável exclusivamente por indicadores via COUNT.
Não contém regras de negócio.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.compra_concreto import CompraConcreto
from app.models.fornecedor import Fornecedor
from app.models.funcionario import Funcionario
from app.models.produto import Produto
from app.models.producao import Producao


class DashboardRepository:
    """Consultas agregadas para indicadores do dashboard."""

    def __init__(self, db: Session) -> None:
        """Inicializa o repository com a sessão do banco."""
        self.db = db

    def contar_clientes_ativos(self) -> int:
        """Retorna o total de clientes ativos."""
        return (
            self.db.query(func.count(Cliente.id))
            .filter(Cliente.ativo.is_(True))
            .scalar()
            or 0
        )

    def contar_fornecedores_ativos(self) -> int:
        """Retorna o total de fornecedores ativos."""
        return (
            self.db.query(func.count(Fornecedor.id))
            .filter(Fornecedor.ativo.is_(True))
            .scalar()
            or 0
        )

    def contar_funcionarios_ativos(self) -> int:
        """Retorna o total de funcionários ativos."""
        return (
            self.db.query(func.count(Funcionario.id))
            .filter(Funcionario.ativo.is_(True))
            .scalar()
            or 0
        )

    def contar_produtos_ativos(self) -> int:
        """Retorna o total de produtos ativos."""
        return (
            self.db.query(func.count(Produto.id))
            .filter(Produto.ativo.is_(True))
            .scalar()
            or 0
        )

    def contar_producoes(self) -> int:
        """Retorna o total de produções ativas."""
        return (
            self.db.query(func.count(Producao.id))
            .filter(Producao.ativo.is_(True))
            .scalar()
            or 0
        )

    def contar_compras_concreto(self) -> int:
        """Retorna o total de compras de concreto ativas."""
        return (
            self.db.query(func.count(CompraConcreto.id))
            .filter(CompraConcreto.ativo.is_(True))
            .scalar()
            or 0
        )
