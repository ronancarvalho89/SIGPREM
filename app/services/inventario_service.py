"""
Service de Inventário — regras de negócio (COMMIT 0073).

Não lança HTTPException. Exceções de domínio são mapeadas na API.
No futuro existirá um middleware/handler global de exceções.
"""

from decimal import Decimal
from typing import Any
from typing import Optional

from app.models.inventario import Inventario
from app.models.item_inventario import ItemInventario
from app.models.movimento_estoque import TipoMovimentoEstoque
from app.repositories.inventario_repository import InventarioRepository
from app.repositories.item_inventario_repository import ItemInventarioRepository
from app.repositories.movimento_estoque_repository import (
    MovimentoEstoqueRepository,
)
from app.schemas.inventario import InventarioCreate
from app.schemas.inventario import InventarioUpdate
from app.schemas.item_inventario import ItemInventarioCreate
from app.schemas.movimento_estoque import MovimentoEstoqueCreate
from app.services.item_inventario_service import ItemInventarioService
from app.services.movimento_estoque_service import MovimentoEstoqueService


class InventarioNaoEncontrado(Exception):
    """Inventário ativo não encontrado."""


class InventarioService:
    """Regras de negócio do cadastro de inventários."""

    def __init__(self, repository: InventarioRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository
        self._item_inventario_service: Optional[ItemInventarioService] = None
        self._estoque_service: Optional[MovimentoEstoqueService] = None

    @property
    def item_inventario_service(self) -> ItemInventarioService:
        """Service de itens de inventário (lazy) compartilhando a mesma sessão."""
        if self._item_inventario_service is None:
            self._item_inventario_service = ItemInventarioService(
                ItemInventarioRepository(self.repository.db)
            )
        return self._item_inventario_service

    @item_inventario_service.setter
    def item_inventario_service(self, value: ItemInventarioService) -> None:
        """Permite injeção/substituição em testes."""
        self._item_inventario_service = value

    @property
    def estoque_service(self) -> MovimentoEstoqueService:
        """Service de estoque (lazy) compartilhando a mesma sessão."""
        if self._estoque_service is None:
            self._estoque_service = MovimentoEstoqueService(
                MovimentoEstoqueRepository(self.repository.db)
            )
        return self._estoque_service

    @estoque_service.setter
    def estoque_service(self, value: MovimentoEstoqueService) -> None:
        """Permite injeção/substituição em testes."""
        self._estoque_service = value

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
        """Retorna inventário ativo por id ou levanta InventarioNaoEncontrado."""
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

        Preenche quantidade_sistema com o saldo atual do produto
        via MovimentoEstoqueService e cria o item via ItemInventarioService.
        """
        inventario = self.buscar_por_id(inventario_id)

        quantidade_sistema = self.estoque_service.saldo_produto(
            dados.produto_id
        )

        dados_item = dados.model_copy(
            update={
                "inventario_id": inventario.id,
                "quantidade_sistema": quantidade_sistema,
            }
        )

        return self.item_inventario_service.criar(dados_item)

    def concluir(self, inventario_id: int) -> Inventario:
        """
        Conclui o inventário e gera ajustes de estoque.

        Para cada item com diferença diferente de zero, registra
        ENTRADA ou SAÍDA via MovimentoEstoqueService.
        """
        inventario = self.buscar_por_id(inventario_id)
        itens = self.item_inventario_service.listar_por_inventario(
            inventario_id
        )

        for item in itens:
            self._registrar_ajuste_se_necessario(inventario, item)

        return inventario

    def _registrar_ajuste_se_necessario(
        self,
        inventario: Inventario,
        item: ItemInventario,
    ) -> None:
        """Registra movimento de ajuste quando a diferença for diferente de zero."""
        diferenca = Decimal(str(item.diferenca))

        if diferenca == 0:
            return

        if diferenca > 0:
            tipo = TipoMovimentoEstoque.ENTRADA
            quantidade = diferenca
        else:
            tipo = TipoMovimentoEstoque.SAIDA
            quantidade = abs(diferenca)

        self.estoque_service.criar(
            MovimentoEstoqueCreate(
                data=inventario.data_inventario,
                produto_id=item.produto_id,
                quantidade=quantidade,
                tipo=tipo,
                observacao=f"Ajuste inventário {inventario.id}",
            )
        )
