"""
Service de ItemVenda — regras de negócio (COMMIT 0029).

Não lança HTTPException. Exceções de domínio são mapeadas na API.
No futuro existirá um middleware/handler global de exceções.
"""

from typing import Any

from app.models.item_venda import ItemVenda
from app.repositories.item_venda_repository import ItemVendaRepository
from app.schemas.item_venda import ItemVendaCreate
from app.schemas.item_venda import ItemVendaUpdate


class ItemVendaNaoEncontrado(Exception):
    """Item de venda ativo não encontrado."""


class ItemVendaService:
    """Regras de negócio do cadastro de itens de venda."""

    def __init__(self, repository: ItemVendaRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository

    def criar(self, dados: ItemVendaCreate) -> ItemVenda:
        """Cria um novo item de venda."""
        item = ItemVenda(**dados.model_dump())
        return self.repository.criar(item)

    def listar(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ItemVenda]:
        """Lista itens ativos com paginação."""
        return self.repository.listar(skip=skip, limit=limit)

    def buscar_por_id(self, item_id: int) -> ItemVenda:
        """Retorna item ativo por id ou levanta exceção."""
        item = self.repository.buscar_por_id(item_id)

        if item is None:
            raise ItemVendaNaoEncontrado("Item de venda não encontrado.")

        return item

    def atualizar(
        self,
        item_id: int,
        dados: ItemVendaUpdate,
    ) -> ItemVenda:
        """Atualiza campos informados do item (exclude_unset)."""
        item = self.buscar_por_id(item_id)
        campos: dict[str, Any] = dados.model_dump(exclude_unset=True)

        for campo, valor in campos.items():
            setattr(item, campo, valor)

        return self.repository.atualizar(item)

    def excluir(self, item_id: int) -> ItemVenda:
        """Realiza exclusão lógica do item (ativo = False)."""
        item = self.buscar_por_id(item_id)
        return self.repository.inativar(item)
