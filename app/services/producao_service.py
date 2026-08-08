"""
Service de Produção — regras de negócio (COMMIT 0018).

Não lança HTTPException. Exceções de domínio são mapeadas na API.
No futuro existirá um middleware/handler global de exceções.
"""

from decimal import Decimal
from typing import Any

from app.models.compra_concreto import CompraConcreto
from app.models.movimento_estoque import MovimentoEstoque
from app.models.movimento_estoque import TipoMovimentoEstoque
from app.models.produto import Produto
from app.models.producao import Producao
from app.repositories.producao_repository import ProducaoRepository
from app.schemas.producao import ProducaoCreate
from app.schemas.producao import ProducaoUpdate

# from app.models.funcionario_valor_produto import FuncionarioValorProduto


class ProducaoNaoEncontrada(Exception):
    """Produção ativa não encontrada."""


class SaldoConcretoInsuficiente(Exception):
    """Saldo de concreto insuficiente para a produção."""


class ProducaoDadosInvalidos(Exception):
    """Referências inválidas para criação da produção."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ProducaoService:
    """Regras de negócio do cadastro de produção."""

    def __init__(self, repository: ProducaoRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository

    def criar(self, dados: ProducaoCreate) -> Producao:
        """
        Cria produção, consome concreto e gera entrada de estoque.

        Produção e movimento de estoque são gravados na mesma transação.
        """
        compra = self.repository.db.get(
            CompraConcreto,
            dados.compra_concreto_id,
        )

        produto = self.repository.db.get(
            Produto,
            dados.produto_id,
        )

        if compra is None or not compra.ativo:
            raise ProducaoDadosInvalidos(
                "Compra de concreto não encontrada."
            )

        if produto is None or not produto.ativo:
            raise ProducaoDadosInvalidos("Produto não encontrado.")

        concreto = (
            Decimal(dados.quantidade_produzida)
            * Decimal(produto.concreto_por_unidade)
        )

        if compra.saldo < concreto:
            raise SaldoConcretoInsuficiente(
                "Saldo insuficiente de concreto."
            )

        compra.saldo -= concreto

        #
        # O cálculo do pagamento será substituído
        # pela tabela FuncionarioValorProduto
        #

        valor = Decimal("0.00")

        producao = Producao(
            data=dados.data,
            funcionario_id=dados.funcionario_id,
            produto_id=dados.produto_id,
            compra_concreto_id=dados.compra_concreto_id,
            quantidade_produzida=dados.quantidade_produzida,
            concreto_consumido=concreto,
            valor_producao=valor,
            observacao=dados.observacao,
        )

        self.repository.db.add(producao)
        self.repository.db.flush()

        movimento = MovimentoEstoque(
            data=producao.data,
            produto_id=producao.produto_id,
            quantidade=producao.quantidade_produzida,
            tipo=TipoMovimentoEstoque.ENTRADA,
            producao_id=producao.id,
            observacao="Entrada automática gerada pela produção.",
        )

        self.repository.db.add(movimento)

        #
        # Próximo commit:
        #
        # gerar pagamento funcionário
        #

        return self.repository.criar(producao)

    def listar(self, skip: int = 0, limit: int = 50) -> list[Producao]:
        """Lista produções ativas com paginação."""
        return self.repository.listar(skip=skip, limit=limit)

    def buscar_por_id(self, producao_id: int) -> Producao:
        """Retorna produção ativa por id ou levanta ProducaoNaoEncontrada."""
        producao = self.repository.buscar_por_id(producao_id)

        if producao is None:
            raise ProducaoNaoEncontrada("Produção não encontrada.")

        return producao

    def atualizar(
        self,
        producao_id: int,
        dados: ProducaoUpdate,
    ) -> Producao:
        """Atualiza campos permitidos da produção (exclude_unset)."""
        producao = self.buscar_por_id(producao_id)
        campos: dict[str, Any] = dados.model_dump(exclude_unset=True)

        for campo, valor in campos.items():
            setattr(producao, campo, valor)

        return self.repository.atualizar(producao)

    def excluir(self, producao_id: int) -> Producao:
        """Realiza exclusão lógica da produção (ativo = False)."""
        producao = self.buscar_por_id(producao_id)
        return self.repository.inativar(producao)
