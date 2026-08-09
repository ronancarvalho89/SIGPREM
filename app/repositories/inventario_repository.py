"""
Repository de Inventário — acesso a dados (COMMIT 0073).

Responsável exclusivamente por operações de persistência.
Não contém regras de negócio.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.inventario import Inventario


class InventarioRepository:
    """Acesso ao banco de dados para a entidade Inventario."""

    def __init__(self, db: Session) -> None:
        """Inicializa o repository com a sessão do banco."""
        self.db = db

    def criar(self, inventario: Inventario) -> Inventario:
        """Persiste um novo inventário."""
        self.db.add(inventario)
        self.db.commit()
        self.db.refresh(inventario)
        return inventario

    def listar(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Inventario]:
        """Lista inventários ativos com paginação (data_inventario DESC)."""
        return (
            self.db.query(Inventario)
            .filter(Inventario.ativo.is_(True))
            .order_by(Inventario.data_inventario.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def buscar_por_id(self, inventario_id: int) -> Optional[Inventario]:
        """Busca inventário ativo pelo identificador."""
        return (
            self.db.query(Inventario)
            .filter(
                Inventario.id == inventario_id,
                Inventario.ativo.is_(True),
            )
            .first()
        )

    def atualizar(self, inventario: Inventario) -> Inventario:
        """Persiste alterações em um inventário existente."""
        self.db.commit()
        self.db.refresh(inventario)
        return inventario

    def inativar(self, inventario: Inventario) -> Inventario:
        """
        Realiza exclusão lógica (soft delete).

        Nunca remove o registro fisicamente.
        """
        inventario.ativo = False
        self.db.commit()
        self.db.refresh(inventario)
        return inventario
