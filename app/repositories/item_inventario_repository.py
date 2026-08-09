"""
Repository de ItemInventario — acesso a dados (COMMIT 0066).

Responsável exclusivamente por operações de persistência.
Não contém regras de negócio.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.item_inventario import ItemInventario


class ItemInventarioRepository:
    """Acesso ao banco de dados para a entidade ItemInventario."""

    def __init__(self, db: Session) -> None:
        """Inicializa o repository com a sessão do banco."""
        self.db = db

    def criar(self, item: ItemInventario) -> ItemInventario:
        """Persiste um novo item de inventário."""
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def listar(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ItemInventario]:
        """Lista itens ativos com paginação (id DESC)."""
        return (
            self.db.query(ItemInventario)
            .filter(ItemInventario.ativo.is_(True))
            .order_by(ItemInventario.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def buscar_por_id(self, item_id: int) -> Optional[ItemInventario]:
        """Busca item ativo pelo identificador."""
        return (
            self.db.query(ItemInventario)
            .filter(
                ItemInventario.id == item_id,
                ItemInventario.ativo.is_(True),
            )
            .first()
        )

    def atualizar(self, item: ItemInventario) -> ItemInventario:
        """Persiste alterações em um item existente."""
        self.db.commit()
        self.db.refresh(item)
        return item

    def inativar(self, item: ItemInventario) -> ItemInventario:
        """
        Realiza exclusão lógica (soft delete).

        Nunca remove o registro fisicamente.
        """
        item.ativo = False
        self.db.commit()
        self.db.refresh(item)
        return item
