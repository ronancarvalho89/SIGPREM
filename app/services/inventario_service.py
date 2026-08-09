"""
Service de Inventário — regras de negócio (EPIC 002).

Não lança HTTPException. Exceções de domínio são mapeadas na API.
No futuro existirá um middleware/handler global de exceções.
"""

from decimal import Decimal
from typing import Any
from typing import Optional

from app.models.inventario import Inventario
from app.models.item_inventario import ItemInventario
from app.models.movimento_estoque import TipoMovimentoEstoque
from app.repositories.auditoria_repository import AuditoriaRepository
from app.repositories.inventario_repository import InventarioRepository
from app.repositories.item_inventario_repository import ItemInventarioRepository
from app.repositories.movimento_estoque_repository import (
    MovimentoEstoqueRepository,
)
from app.schemas.auditoria import AuditoriaCreate
from app.schemas.inventario import InventarioCreate
from app.schemas.inventario import InventarioUpdate
from app.schemas.item_inventario import ItemInventarioCreate
from app.schemas.movimento_estoque import MovimentoEstoqueCreate
from app.services.auditoria_service import AuditoriaService
from app.services.item_inventario_service import ItemInventarioService
from app.services.movimento_estoque_service import MovimentoEstoqueService


STATUS_INVENTARIO_ABERTO = "aberto"
STATUS_INVENTARIO_CONCLUIDO = "concluido"
STATUS_INVENTARIO_VALIDOS = {
    STATUS_INVENTARIO_ABERTO,
    STATUS_INVENTARIO_CONCLUIDO,
}


class InventarioNaoEncontrado(Exception):
    """Inventário ativo não encontrado."""


class InventarioStatusInvalido(Exception):
    """Status de inventário informado é inválido."""


class InventarioJaConcluido(Exception):
    """Operação inválida porque o inventário já foi concluído."""


class InventarioService:
    """Regras de negócio do cadastro de inventários."""

    def __init__(self, repository: InventarioRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository
        self._item_inventario_service: Optional[ItemInventarioService] = None
        self._estoque_service: Optional[MovimentoEstoqueService] = None
        self._auditoria_service: Optional[AuditoriaService] = None

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

    @property
    def auditoria_service(self) -> AuditoriaService:
        """Service de auditoria (lazy) compartilhando a mesma sessão."""
        if self._auditoria_service is None:
            self._auditoria_service = AuditoriaService(
                AuditoriaRepository(self.repository.db)
            )
        return self._auditoria_service

    @auditoria_service.setter
    def auditoria_service(self, value: AuditoriaService) -> None:
        """Permite injeção/substituição em testes."""
        self._auditoria_service = value

    def criar(self, dados: InventarioCreate) -> Inventario:
        """Cria um novo inventário com status inicial aberto."""
        inventario = Inventario(
            **dados.model_dump(),
            status=STATUS_INVENTARIO_ABERTO,
        )
        inventario = self.repository.criar(inventario)
        self._registrar_auditoria(
            usuario_id=inventario.usuario_id,
            acao="criar",
            entidade="Inventario",
            entidade_id=inventario.id,
            descricao=f"Inventário {inventario.id} criado.",
        )
        return inventario

    def listar(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Inventario]:
        """Lista inventários ativos com paginação."""
        return self.repository.listar(skip=skip, limit=limit)

    def listar_por_status(
        self,
        status: str,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Inventario]:
        """Lista inventários ativos filtrados por status."""
        status_normalizado = self._normalizar_status(status)
        return self.repository.listar_por_status(
            status_normalizado,
            skip=skip,
            limit=limit,
        )

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
        self._garantir_aberto(inventario)
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
        self._garantir_aberto(inventario)

        quantidade_sistema = self.estoque_service.saldo_produto(
            dados.produto_id
        )

        dados_item = dados.model_copy(
            update={
                "inventario_id": inventario.id,
                "quantidade_sistema": quantidade_sistema,
            }
        )

        item = self.item_inventario_service.criar(dados_item)
        self._registrar_auditoria(
            usuario_id=inventario.usuario_id,
            acao="adicionar_item",
            entidade="ItemInventario",
            entidade_id=item.id,
            descricao=(
                f"Item {item.id} adicionado ao inventário "
                f"{inventario.id}."
            ),
        )
        return item

    def concluir(self, inventario_id: int) -> Inventario:
        """
        Conclui o inventário e gera ajustes de estoque.

        Para cada item com diferença diferente de zero, registra
        ENTRADA ou SAÍDA via MovimentoEstoqueService.
        """
        inventario = self.buscar_por_id(inventario_id)
        self._garantir_aberto(inventario)

        itens = self.item_inventario_service.listar_por_inventario(
            inventario_id
        )

        for item in itens:
            self._registrar_ajuste_se_necessario(inventario, item)

        inventario.status = STATUS_INVENTARIO_CONCLUIDO
        inventario = self.repository.atualizar(inventario)
        self._registrar_auditoria(
            usuario_id=inventario.usuario_id,
            acao="concluir",
            entidade="Inventario",
            entidade_id=inventario.id,
            descricao=f"Inventário {inventario.id} concluído.",
        )
        return inventario

    def _garantir_aberto(self, inventario: Inventario) -> None:
        """Impede alterações em inventário já concluído."""
        if inventario.status == STATUS_INVENTARIO_CONCLUIDO:
            raise InventarioJaConcluido(
                "Inventário já concluído. Operação não permitida."
            )

    def _normalizar_status(self, status: str) -> str:
        """Valida e normaliza o status informado."""
        normalizado = status.strip().lower().replace("í", "i")

        if normalizado not in STATUS_INVENTARIO_VALIDOS:
            raise InventarioStatusInvalido(
                "Status inválido. Use 'aberto' ou 'concluido'."
            )

        return normalizado

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

        movimento = self.estoque_service.criar(
            MovimentoEstoqueCreate(
                data=inventario.data_inventario,
                produto_id=item.produto_id,
                quantidade=quantidade,
                tipo=tipo,
                observacao=f"Ajuste inventário {inventario.id}",
            )
        )
        self._registrar_auditoria(
            usuario_id=inventario.usuario_id,
            acao="ajuste_estoque",
            entidade="MovimentoEstoque",
            entidade_id=movimento.id,
            descricao=(
                f"Ajuste de estoque do inventário {inventario.id} "
                f"para o produto {item.produto_id}."
            ),
        )

    def _registrar_auditoria(
        self,
        acao: str,
        entidade: str,
        entidade_id: int,
        descricao: str,
        usuario_id: Optional[int] = None,
    ) -> None:
        """Registra auditoria da operação de inventário via AuditoriaService."""
        try:
            self.auditoria_service.registrar(
                AuditoriaCreate(
                    usuario_id=usuario_id,
                    modulo="inventario",
                    acao=acao,
                    entidade=entidade,
                    entidade_id=entidade_id,
                    descricao=descricao,
                )
            )
        except Exception:
            return
