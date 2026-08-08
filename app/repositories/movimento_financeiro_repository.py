"""
Repository de Movimento Financeiro — acesso a dados (COMMIT 0024).

Responsável exclusivamente por operações de persistência.
Não contém regras de negócio.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.movimento_financeiro import MovimentoFinanceiro


class MovimentoFinanceiroRepository:
    """Acesso ao banco de dados para a entidade MovimentoFinanceiro."""

    def __init__(self, db: Session) -> None:
        """Inicializa o repository com a sessão do banco."""
        self.db = db

    def criar(
        self,
        movimento: MovimentoFinanceiro,
    ) -> MovimentoFinanceiro:
        """Persiste um novo movimento financeiro."""
        self.db.add(movimento)
        self.db.commit()
        self.db.refresh(movimento)
        return movimento

    def listar(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[MovimentoFinanceiro]:
        """Lista movimentos ativos com paginação (data_movimento DESC)."""
        return (
            self.db.query(MovimentoFinanceiro)
            .filter(MovimentoFinanceiro.ativo.is_(True))
            .order_by(MovimentoFinanceiro.data_movimento.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def listar_ativos(self) -> list[MovimentoFinanceiro]:
        """Lista todos os movimentos financeiros ativos (sem paginação)."""
        return (
            self.db.query(MovimentoFinanceiro)
            .filter(MovimentoFinanceiro.ativo.is_(True))
            .all()
        )

    def buscar_por_id(
        self,
        movimento_id: int,
    ) -> Optional[MovimentoFinanceiro]:
        """Busca movimento ativo pelo identificador."""
        return (
            self.db.query(MovimentoFinanceiro)
            .filter(
                MovimentoFinanceiro.id == movimento_id,
                MovimentoFinanceiro.ativo.is_(True),
            )
            .first()
        )

    def atualizar(
        self,
        movimento: MovimentoFinanceiro,
    ) -> MovimentoFinanceiro:
        """Persiste alterações em um movimento existente."""
        self.db.commit()
        self.db.refresh(movimento)
        return movimento

    def inativar(
        self,
        movimento: MovimentoFinanceiro,
    ) -> MovimentoFinanceiro:
        """
        Realiza exclusão lógica (soft delete).

        Nunca remove o registro fisicamente.
        """
        movimento.ativo = False
        self.db.commit()
        self.db.refresh(movimento)
        return movimento
