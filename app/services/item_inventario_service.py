"""
Service de ItemInventario — regras de negócio (COMMIT 0066).

Não lança HTTPException. Exceções de domínio são mapeadas na API.
No futuro existirá um middleware/handler global de exceções.
"""

from typing import Any

from app.models.item_inventario import ItemInventario
from app.repositories.item_inventario_repository import ItemInventarioRepository
from app.schemas.item_inventario import ItemInventarioCreate
from app.schemas.item_inventario import ItemInventarioUpdate


class ItemInventarioNaoEncontrado(Exception):
    """Item de inventário ativo não encontrado."""


class ItemInventarioService:
    """Regras de negócio do cadastro de itens de inventário."""

    def __init__(self, repository: ItemInventarioRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository

    def criar(self, dados: ItemInventarioCreate) -> ItemInventario:
        """Cria um novo item de inventário."""
        item = ItemInventario(**dados.model_dump())
        return self.repository.criar(item)

    def listar(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ItemInventario]:
        """Lista itens ativos com paginação."""
        return self.repository.listar(skip=skip, limit=limit)

    def buscar_por_id(self, item_id: int) -> ItemInventario:
        """Retorna item ativo por id ou levanta exceção."""
        item = self.repository.buscar_por_id(item_id)

        if item is None:
            raise ItemInventarioNaoEncontrado(
                "Item de inventário não encontrado."
            )

        return item

    def atualizar(
        self,
        item_id: int,
        dados: ItemInventarioUpdate,
    ) -> ItemInventario:
        """Atualiza campos informados do item (exclude_unset)."""
        item = self.buscar_por_id(item_id)
        campos: dict[str, Any] = dados.model_dump(exclude_unset=True)

        for campo, valor in campos.items():
            setattr(item, campo, valor)

        return self.repository.atualizar(item)

    def excluir(self, item_id: int) -> ItemInventario:
        """Realiza exclusão lógica do item (ativo = False)."""
        item = self.buscar_por_id(item_id)
        return self.repository.inativar(item)
