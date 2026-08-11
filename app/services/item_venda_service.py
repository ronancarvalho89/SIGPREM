"""
Service de ItemVenda — regras de negócio (EPIC 004 / Pacote 4.3).

Itens de venda fazem parte do agregado Venda.
Criação completa (itens + estoque + financeiro) ocorre apenas via
VendaService.criar / POST /vendas.

Mutações independentes (criar/atualizar/excluir) são bloqueadas para
evitar inconsistência de estoque, total e financeiro.
Estorno/ajuste de itens existentes fica para o Pacote 4.6.
"""

from app.models.item_venda import ItemVenda
from app.repositories.item_venda_repository import ItemVendaRepository
from app.schemas.item_venda import ItemVendaCreate
from app.schemas.item_venda import ItemVendaUpdate


class ItemVendaNaoEncontrado(Exception):
    """Item de venda ativo não encontrado."""


class OperacaoItemVendaNaoPermitida(Exception):
    """
    Mutação independente de ItemVenda não é permitida.

    Use POST /vendas com itens aninhados para criar a venda completa.
    """


_MSG_MUTACAO = (
    "Itens de venda não podem ser criados, alterados ou excluídos "
    "independentemente. Utilize POST /vendas com itens aninhados. "
    "Ajustes com estorno de estoque/financeiro serão tratados na "
    "política de update/delete da Venda."
)


class ItemVendaService:
    """Consulta de itens de venda; mutações indep. bloqueadas."""

    def __init__(self, repository: ItemVendaRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository

    def criar(self, dados: ItemVendaCreate) -> ItemVenda:
        """Bloqueado: criação somente via VendaService.criar."""
        _ = dados
        raise OperacaoItemVendaNaoPermitida(_MSG_MUTACAO)

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
        """
        Bloqueado neste pacote.

        Alterar quantidade/preço exigiria estorno e nova baixa —
        política do Pacote 4.6.
        """
        _ = item_id, dados
        raise OperacaoItemVendaNaoPermitida(_MSG_MUTACAO)

    def excluir(self, item_id: int) -> ItemVenda:
        """
        Bloqueado neste pacote.

        Inativar item sem compensar estoque/financeiro deixa a venda
        inconsistente — política do Pacote 4.6.
        """
        _ = item_id
        raise OperacaoItemVendaNaoPermitida(_MSG_MUTACAO)
