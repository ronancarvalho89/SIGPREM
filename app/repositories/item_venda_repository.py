"""
Repository de ItemVenda — acesso a dados (COMMIT 0029).

Responsável exclusivamente por operações de persistência.
Não contém regras de negócio.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.item_venda import ItemVenda


class ItemVendaRepository:
    """Acesso ao banco de dados para a entidade ItemVenda."""

    def __init__(self, db: Session) -> None:
        """Inicializa o repository com a sessão do banco."""
        self.db = db

    def criar(self, item: ItemVenda) -> ItemVenda:
        """Persiste um novo item de venda."""
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def listar(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ItemVenda]:
        """Lista itens ativos com paginação (id DESC)."""
        return (
            self.db.query(ItemVenda)
            .filter(ItemVenda.ativo.is_(True))
            .order_by(ItemVenda.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def buscar_por_id(self, item_id: int) -> Optional[ItemVenda]:
        """Busca item ativo pelo identificador."""
        return (
            self.db.query(ItemVenda)
            .filter(
                ItemVenda.id == item_id,
                ItemVenda.ativo.is_(True),
            )
            .first()
        )

    def atualizar(self, item: ItemVenda) -> ItemVenda:
        """Persiste alterações em um item existente."""
        self.db.commit()
        self.db.refresh(item)
        return item

    def inativar(self, item: ItemVenda) -> ItemVenda:
        """
        Realiza exclusão lógica (soft delete).

        Nunca remove o registro fisicamente.
        """
        item.ativo = False
        self.db.commit()
        self.db.refresh(item)
        return item
