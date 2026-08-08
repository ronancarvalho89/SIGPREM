"""
Repository de Movimento de Estoque — acesso a dados (COMMIT 0016).

Responsável exclusivamente por operações de persistência.
Não contém regras de negócio.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.movimento_estoque import MovimentoEstoque


class MovimentoEstoqueRepository:
    """Acesso ao banco de dados para a entidade MovimentoEstoque."""

    def __init__(self, db: Session) -> None:
        """Inicializa o repository com a sessão do banco."""
        self.db = db

    def criar(self, movimento: MovimentoEstoque) -> MovimentoEstoque:
        """Persiste um novo movimento de estoque."""
        self.db.add(movimento)
        self.db.commit()
        self.db.refresh(movimento)
        return movimento

    def listar(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[MovimentoEstoque]:
        """Lista movimentos ativos com paginação (data DESC)."""
        return (
            self.db.query(MovimentoEstoque)
            .filter(MovimentoEstoque.ativo.is_(True))
            .order_by(MovimentoEstoque.data.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def buscar_por_id(
        self,
        movimento_id: int,
    ) -> Optional[MovimentoEstoque]:
        """Busca movimento ativo pelo identificador."""
        return (
            self.db.query(MovimentoEstoque)
            .filter(
                MovimentoEstoque.id == movimento_id,
                MovimentoEstoque.ativo.is_(True),
            )
            .first()
        )

    def atualizar(self, movimento: MovimentoEstoque) -> MovimentoEstoque:
        """Persiste alterações em um movimento existente."""
        self.db.commit()
        self.db.refresh(movimento)
        return movimento

    def inativar(self, movimento: MovimentoEstoque) -> MovimentoEstoque:
        """
        Realiza exclusão lógica (soft delete).

        Nunca remove o registro fisicamente.
        """
        movimento.ativo = False
        self.db.commit()
        self.db.refresh(movimento)
        return movimento
