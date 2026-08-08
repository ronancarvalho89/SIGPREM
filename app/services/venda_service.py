"""
Service de Venda — regras de negócio (COMMIT 0034).

Não lança HTTPException. Exceções de domínio são mapeadas na API.
No futuro existirá um middleware/handler global de exceções.
"""

from decimal import Decimal
from typing import Any
from typing import Optional
from uuid import UUID

from app.models.item_venda import ItemVenda
from app.models.movimento_estoque import MovimentoEstoque
from app.models.movimento_estoque import TipoMovimentoEstoque
from app.models.movimento_financeiro import MovimentoFinanceiro
from app.models.movimento_financeiro import TipoMovimentoFinanceiro
from app.models.venda import Venda
from app.repositories.movimento_estoque_repository import (
    MovimentoEstoqueRepository,
)
from app.repositories.venda_repository import VendaRepository
from app.schemas.venda import VendaCreate
from app.schemas.venda import VendaUpdate
from app.services.movimento_estoque_service import MovimentoEstoqueService


class VendaNaoEncontrada(Exception):
    """Venda ativa não encontrada."""


class VendaDuplicada(Exception):
    """Venda com número já cadastrado."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class EstoqueInsuficiente(Exception):
    """Saldo de estoque insuficiente para a venda."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class VendaService:
    """Regras de negócio do cadastro de vendas."""

    def __init__(self, repository: VendaRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository
        self.estoque_service = MovimentoEstoqueService(
            MovimentoEstoqueRepository(repository.db)
        )

    def criar(
        self,
        dados: VendaCreate,
        itens: Optional[list[Any]] = None,
    ) -> Venda:
        """
        Cria venda, ItemVenda, baixa de estoque e MovimentoFinanceiro
        na mesma transação.
        """
        self._validar_numero_unico(dados.numero)

        itens_venda = self._resolver_itens(dados, itens)

        venda = Venda(**dados.model_dump())

        try:
            self.repository.db.add(venda)
            self.repository.db.flush()

            total_venda = Decimal("0")
            itens_criados: list[ItemVenda] = []

            for item_dados in itens_venda:
                produto_id, quantidade, valor_unitario = (
                    self._extrair_campos_item(item_dados)
                )
                valor_total_item = quantidade * valor_unitario

                item = ItemVenda(
                    venda_id=venda.id,
                    produto_id=produto_id,
                    quantidade=quantidade,
                    valor_unitario=valor_unitario,
                    valor_total=valor_total_item,
                )
                self.repository.db.add(item)
                itens_criados.append(item)
                total_venda += valor_total_item

            if itens_venda:
                venda.valor_total = total_venda

            self._baixar_estoque(venda, itens_criados)

            movimento = MovimentoFinanceiro(
                tipo=TipoMovimentoFinanceiro.VENDA,
                data_movimento=venda.data_venda,
                valor=venda.valor_total,
                descricao="Venda",
                observacao=(
                    f"Cliente ID {venda.cliente_id}. "
                    f"Venda ID {venda.id}."
                ),
            )

            self.repository.db.add(movimento)

            return self.repository.criar(venda)

        except Exception:
            self.repository.db.rollback()
            raise

    def listar(self, skip: int = 0, limit: int = 50) -> list[Venda]:
        """Lista vendas ativas com paginação."""
        return self.repository.listar(skip=skip, limit=limit)

    def buscar_por_id(self, venda_id: UUID) -> Venda:
        """Retorna venda ativa por id ou levanta VendaNaoEncontrada."""
        venda = self.repository.buscar_por_id(venda_id)

        if venda is None:
            raise VendaNaoEncontrada("Venda não encontrada.")

        return venda

    def atualizar(self, venda_id: UUID, dados: VendaUpdate) -> Venda:
        """Atualiza campos informados da venda (exclude_unset)."""
        venda = self.buscar_por_id(venda_id)
        campos: dict[str, Any] = dados.model_dump(exclude_unset=True)

        if "numero" in campos:
            self._validar_numero_unico(
                campos["numero"],
                venda_id=venda_id,
            )

        for campo, valor in campos.items():
            setattr(venda, campo, valor)

        return self.repository.atualizar(venda)

    def excluir(self, venda_id: UUID) -> Venda:
        """Realiza exclusão lógica da venda (ativo = False)."""
        venda = self.buscar_por_id(venda_id)
        return self.repository.inativar(venda)

    def _validar_numero_unico(
        self,
        numero: str,
        venda_id: Optional[UUID] = None,
    ) -> None:
        """Valida se o número já está em uso por outra venda ativa."""
        existente = self.repository.buscar_por_numero(numero)

        if existente is not None and existente.id != venda_id:
            raise VendaDuplicada(
                "Já existe uma venda cadastrada com este número."
            )

    def _resolver_itens(
        self,
        dados: VendaCreate,
        itens: Optional[list[Any]],
    ) -> list[Any]:
        """Resolve a coleção de itens recebida no fluxo de criação."""
        if itens is not None:
            return list(itens)

        itens_dados = getattr(dados, "itens", None)
        if itens_dados is None:
            return []

        return list(itens_dados)

    def _extrair_campos_item(
        self,
        item_dados: Any,
    ) -> tuple[int, Decimal, Decimal]:
        """Extrai produto_id, quantidade e valor_unitario de um item."""
        if isinstance(item_dados, dict):
            produto_id = int(item_dados["produto_id"])
            quantidade = Decimal(str(item_dados["quantidade"]))
            valor_unitario = Decimal(str(item_dados["valor_unitario"]))
            return produto_id, quantidade, valor_unitario

        produto_id = int(item_dados.produto_id)
        quantidade = Decimal(str(item_dados.quantidade))
        valor_unitario = Decimal(str(item_dados.valor_unitario))
        return produto_id, quantidade, valor_unitario

    def _baixar_estoque(
        self,
        venda: Venda,
        itens: list[ItemVenda],
    ) -> None:
        """
        Valida saldo e gera MovimentoEstoque SAIDA para cada item.
        """
        reservado: dict[int, Decimal] = {}

        for item in itens:
            saldo = self.estoque_service.saldo_produto(item.produto_id)
            saldo_disponivel = saldo - reservado.get(
                item.produto_id,
                Decimal("0"),
            )

            if saldo_disponivel < item.quantidade:
                raise EstoqueInsuficiente(
                    f"Estoque insuficiente para o produto "
                    f"{item.produto_id}. "
                    f"Saldo disponível: {saldo_disponivel}."
                )

            movimento_estoque = MovimentoEstoque(
                data=venda.data_venda,
                produto_id=item.produto_id,
                quantidade=item.quantidade,
                tipo=TipoMovimentoEstoque.SAIDA,
                observacao=f"Venda {venda.numero}",
            )
            self.repository.db.add(movimento_estoque)

            reservado[item.produto_id] = (
                reservado.get(item.produto_id, Decimal("0"))
                + Decimal(str(item.quantidade))
            )
