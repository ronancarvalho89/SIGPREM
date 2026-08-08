"""
Service de Dashboard — indicadores gerenciais (COMMIT 0041).

Não lança HTTPException.
Centraliza consolidações a partir dos Services existentes.
"""

from decimal import Decimal
from typing import Any

from app.models.movimento_estoque import MovimentoEstoque
from app.models.movimento_estoque import TipoMovimentoEstoque
from app.models.producao import Producao
from app.models.venda import Venda
from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.movimento_estoque_repository import (
    MovimentoEstoqueRepository,
)
from app.repositories.movimento_financeiro_repository import (
    MovimentoFinanceiroRepository,
)
from app.repositories.producao_repository import ProducaoRepository
from app.repositories.venda_repository import VendaRepository
from app.services.movimento_estoque_service import MovimentoEstoqueService
from app.services.movimento_financeiro_service import MovimentoFinanceiroService
from app.services.producao_service import ProducaoService
from app.services.venda_service import VendaService


class DashboardService:
    """Centraliza indicadores gerenciais do ERP."""

    def __init__(self, repository: DashboardRepository) -> None:
        """Inicializa o service e os services dependentes."""
        self.repository = repository
        self.financeiro_service = MovimentoFinanceiroService(
            MovimentoFinanceiroRepository(repository.db)
        )
        self.venda_service = VendaService(
            VendaRepository(repository.db)
        )
        self.producao_service = ProducaoService(
            ProducaoRepository(repository.db)
        )
        self.estoque_service = MovimentoEstoqueService(
            MovimentoEstoqueRepository(repository.db)
        )

    def dashboard(self) -> dict[str, Any]:
        """
        Consolida os indicadores gerenciais do dashboard.

        Retorna fluxo financeiro, comercial, produção e estoque.
        """
        return {
            "fluxo_financeiro": self.financeiro_service.fluxo_caixa(),
            "comercial": self._indicadores_comerciais(),
            "producao": self._indicadores_producao(),
            "estoque": self._indicadores_estoque(),
        }

    def obter_indicadores(self) -> dict[str, int]:
        """Monta os indicadores de contagem já existentes."""
        return {
            "clientes": self.repository.contar_clientes_ativos(),
            "fornecedores": self.repository.contar_fornecedores_ativos(),
            "funcionarios": self.repository.contar_funcionarios_ativos(),
            "produtos": self.repository.contar_produtos_ativos(),
            "producoes": self.repository.contar_producoes(),
            "compras_concreto": self.repository.contar_compras_concreto(),
        }

    def _indicadores_comerciais(self) -> dict[str, Any]:
        """Consolida indicadores comerciais a partir do VendaService."""
        vendas = self._listar_todas_vendas()
        quantidade_vendas = len(vendas)

        if quantidade_vendas == 0:
            zero = Decimal("0")
            return {
                "quantidade_vendas": 0,
                "valor_total_vendas": zero,
                "ticket_medio": zero,
                "maior_venda": zero,
                "menor_venda": zero,
            }

        valores = [Decimal(str(venda.valor_total)) for venda in vendas]
        valor_total_vendas = sum(valores, Decimal("0"))
        ticket_medio = valor_total_vendas / Decimal(quantidade_vendas)

        return {
            "quantidade_vendas": quantidade_vendas,
            "valor_total_vendas": valor_total_vendas,
            "ticket_medio": ticket_medio,
            "maior_venda": max(valores),
            "menor_venda": min(valores),
        }

    def _indicadores_producao(self) -> dict[str, Any]:
        """Consolida indicadores de produção a partir do ProducaoService."""
        producoes = self._listar_todas_producoes()
        quantidade_producoes = len(producoes)

        if quantidade_producoes == 0:
            zero = Decimal("0")
            return {
                "quantidade_producoes": 0,
                "quantidade_total_produzida": zero,
                "custo_total_producao": zero,
                "custo_medio_producao": zero,
            }

        quantidade_total_produzida = sum(
            (Decimal(str(p.quantidade_produzida)) for p in producoes),
            Decimal("0"),
        )
        custo_total_producao = sum(
            (Decimal(str(p.valor_producao)) for p in producoes),
            Decimal("0"),
        )
        custo_medio_producao = (
            custo_total_producao / Decimal(quantidade_producoes)
        )

        return {
            "quantidade_producoes": quantidade_producoes,
            "quantidade_total_produzida": quantidade_total_produzida,
            "custo_total_producao": custo_total_producao,
            "custo_medio_producao": custo_medio_producao,
        }

    def _indicadores_estoque(self) -> dict[str, Any]:
        """Consolida indicadores de estoque a partir do MovimentoEstoqueService."""
        movimentos = self._listar_todos_movimentos_estoque()
        quantidade_movimentos = len(movimentos)

        if quantidade_movimentos == 0:
            zero = Decimal("0")
            return {
                "quantidade_movimentos": 0,
                "total_entradas": zero,
                "total_saidas": zero,
                "saldo_total_estoque": zero,
                "produtos_movimentados": 0,
            }

        total_entradas = Decimal("0")
        total_saidas = Decimal("0")
        produtos: set[int] = set()

        for movimento in movimentos:
            quantidade = Decimal(str(movimento.quantidade))
            produtos.add(movimento.produto_id)

            if movimento.tipo == TipoMovimentoEstoque.ENTRADA:
                total_entradas += quantidade
            elif movimento.tipo == TipoMovimentoEstoque.SAIDA:
                total_saidas += quantidade

        saldo_total_estoque = sum(
            (
                self.estoque_service.saldo_produto(produto_id)
                for produto_id in produtos
            ),
            Decimal("0"),
        )

        return {
            "quantidade_movimentos": quantidade_movimentos,
            "total_entradas": total_entradas,
            "total_saidas": total_saidas,
            "saldo_total_estoque": saldo_total_estoque,
            "produtos_movimentados": len(produtos),
        }

    def _listar_todas_vendas(self) -> list[Venda]:
        """Lista todas as vendas ativas via VendaService (paginado)."""
        return self._listar_paginado(self.venda_service.listar)

    def _listar_todas_producoes(self) -> list[Producao]:
        """Lista todas as produções ativas via ProducaoService (paginado)."""
        return self._listar_paginado(self.producao_service.listar)

    def _listar_todos_movimentos_estoque(self) -> list[MovimentoEstoque]:
        """Lista todos os movimentos ativos via MovimentoEstoqueService."""
        return self._listar_paginado(self.estoque_service.listar)

    def _listar_paginado(self, listar) -> list[Any]:
        """Percorre listagens paginadas de um service até o fim."""
        itens: list[Any] = []
        skip = 0
        limit = 100

        while True:
            lote = listar(skip=skip, limit=limit)
            if not lote:
                break

            itens.extend(lote)

            if len(lote) < limit:
                break

            skip += limit

        return itens
