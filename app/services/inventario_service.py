"""
Service de Inventário — regras de negócio (COMMIT 0068).

Não lança HTTPException. Exceções de domínio são mapeadas na API.
No futuro existirá um middleware/handler global de exceções.
"""

from typing import Any
from typing import Optional

from app.models.inventario import Inventario
from app.models.item_inventario import ItemInventario
from app.repositories.inventario_repository import InventarioRepository
from app.repositories.item_inventario_repository import ItemInventarioRepository
from app.schemas.inventario import InventarioCreate
from app.schemas.inventario import InventarioUpdate
from app.schemas.item_inventario import ItemInventarioCreate
from app.services.item_inventario_service import ItemInventarioService


class InventarioNaoEncontrado(Exception):
    """Inventário ativo não encontrado."""


class InventarioService:
    """Regras de negócio do cadastro de inventários."""

    def __init__(self, repository: InventarioRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository
        self._item_inventario_service: Optional[ItemInventarioService] = None

    @property
    def item_inventario_service(self) -> ItemInventarioService:
        """Service de itens de inventário (lazy)."""
        if self._item_inventario_service is None:
            self._item_inventario_service = ItemInventarioService(
                ItemInventarioRepository(self.repository.db)
            )
        return self._item_inventario_service

    @item_inventario_service.setter
    def item_inventario_service(self, value: ItemInventarioService) -> None:
        """Permite injeção/substituição em testes."""
        self._item_inventario_service = value

    def criar(self, dados: InventarioCreate) -> Inventario:
        """Cria um novo inventário."""
        inventario = Inventario(**dados.model_dump())
        return self.repository.criar(inventario)

    def listar(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Inventario]:
        """Lista inventários ativos com paginação."""
        return self.repository.listar(skip=skip, limit=limit)

    def buscar_por_id(self, inventario_id: int) -> Inventario:
        """Retorna inventário ativo por id ou levanta exceção."""
        inventario = self.repository.buscar_por_id(inventario_id)

        if inventario is None:
            raise InventarioNaoEncontrado("Inventário não encontrado.")

        return inventario

    def atualizar(
        self,
        inventario_id: int,
        dados: InventarioUpdate,
    ) -> Inventario:
        """Atualiza campos informados do inventário (exclude_unset)."""
        inventario = self.buscar_por_id(inventario_id)
        campos: dict[str, Any] = dados.model_dump(exclude_unset=True)

        for campo, valor in campos.items():
            setattr(inventario, campo, valor)

        return self.repository.atualizar(inventario)

    def excluir(self, inventario_id: int) -> Inventario:
        """Realiza exclusão lógica do inventário (ativo = False)."""
        inventario = self.buscar_por_id(inventario_id)
        return self.repository.inativar(inventario)

    def adicionar_item(
        self,
        inventario_id: int,
        dados: ItemInventarioCreate,
    ) -> ItemInventario:
        """
        Associa um ItemInventario a um Inventario existente.

        Valida o inventário e cria o item via ItemInventarioService.
        """
        inventario = self.buscar_por_id(inventario_id)

        dados_item = dados.model_copy(
            update={"inventario_id": inventario.id}
        )

        return self.item_inventario_service.criar(dados_item)
