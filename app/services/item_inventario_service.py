"""
Service de ItemInventario — regras de negócio (EPIC 002).

Não lança HTTPException. Exceções de domínio são mapeadas na API.
No futuro existirá um middleware/handler global de exceções.
"""

from decimal import Decimal
from typing import Any
from typing import Optional

from app.models.item_inventario import ItemInventario
from app.repositories.inventario_repository import InventarioRepository
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
        self._inventario_repository: Optional[InventarioRepository] = None

    @property
    def inventario_repository(self) -> InventarioRepository:
        """Repository de inventário (lazy) compartilhando a mesma sessão."""
        if self._inventario_repository is None:
            self._inventario_repository = InventarioRepository(
                self.repository.db
            )
        return self._inventario_repository

    @inventario_repository.setter
    def inventario_repository(self, value: InventarioRepository) -> None:
        """Permite injeção/substituição em testes."""
        self._inventario_repository = value

    def criar(self, dados: ItemInventarioCreate) -> ItemInventario:
        """Cria um novo item de inventário."""
        self._garantir_inventario_aberto(dados.inventario_id)
        item = ItemInventario(**dados.model_dump())
        return self.repository.criar(item)

    def listar(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ItemInventario]:
        """Lista itens ativos com paginação."""
        return self.repository.listar(skip=skip, limit=limit)

    def listar_por_inventario(
        self,
        inventario_id: int,
    ) -> list[ItemInventario]:
        """Lista itens ativos vinculados a um inventário."""
        return self.repository.listar_por_inventario(inventario_id)

    def buscar_por_id(self, item_id: int) -> ItemInventario:
        """Retorna item ativo por id ou levanta ItemInventarioNaoEncontrado."""
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
        self._garantir_inventario_aberto(item.inventario_id)
        campos: dict[str, Any] = dados.model_dump(exclude_unset=True)

        for campo, valor in campos.items():
            setattr(item, campo, valor)

        return self.repository.atualizar(item)

    def excluir(self, item_id: int) -> ItemInventario:
        """Realiza exclusão lógica do item (ativo = False)."""
        item = self.buscar_por_id(item_id)
        self._garantir_inventario_aberto(item.inventario_id)
        return self.repository.inativar(item)

    def registrar_quantidade_fisica(
        self,
        item_id: int,
        quantidade_fisica: Decimal,
    ) -> ItemInventario:
        """
        Registra a quantidade física contada do item e calcula a diferença.
        """
        item = self.buscar_por_id(item_id)
        self._garantir_inventario_aberto(item.inventario_id)
        item.quantidade_fisica = quantidade_fisica
        self.repository.atualizar(item)
        return self.calcular_diferenca(item_id)

    def calcular_diferenca(self, item_id: int) -> ItemInventario:
        """
        Calcula e persiste a diferença do item.

        diferenca = quantidade_fisica - quantidade_sistema
        """
        item = self.buscar_por_id(item_id)
        self._garantir_inventario_aberto(item.inventario_id)
        item.diferenca = (
            Decimal(str(item.quantidade_fisica))
            - Decimal(str(item.quantidade_sistema))
        )
        return self.repository.atualizar(item)

    def _garantir_inventario_aberto(self, inventario_id: int) -> None:
        """Impede alterações em itens de inventário já concluído."""
        from app.services.inventario_service import (
            STATUS_INVENTARIO_CONCLUIDO,
            InventarioJaConcluido,
            InventarioNaoEncontrado,
        )

        inventario = self.inventario_repository.buscar_por_id(inventario_id)

        if inventario is None:
            raise InventarioNaoEncontrado("Inventário não encontrado.")

        if inventario.status == STATUS_INVENTARIO_CONCLUIDO:
            raise InventarioJaConcluido(
                "Inventário já concluído. Operação não permitida."
            )
