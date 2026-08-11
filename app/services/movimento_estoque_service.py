"""
Service de Movimento de Estoque — regras de negócio (EPIC 004).

Não lança HTTPException. Exceções de domínio são mapeadas na API.
No futuro existirá um middleware/handler global de exceções.
"""

from decimal import Decimal
from typing import Any

from app.models.movimento_estoque import MovimentoEstoque
from app.models.movimento_estoque import TipoMovimentoEstoque
from app.repositories.movimento_estoque_repository import (
    MovimentoEstoqueRepository,
)
from app.schemas.movimento_estoque import MovimentoEstoqueCreate
from app.schemas.movimento_estoque import MovimentoEstoqueUpdate


class MovimentoEstoqueNaoEncontrado(Exception):
    """Movimento de estoque ativo não encontrado."""


class MovimentoEstoqueService:
    """Regras de negócio do cadastro de movimentos de estoque."""

    def __init__(self, repository: MovimentoEstoqueRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository

    def registrar(
        self,
        dados: MovimentoEstoqueCreate,
        *,
        flush: bool = False,
    ) -> MovimentoEstoque:
        """
        Adiciona um movimento de estoque à sessão atual.

        Não realiza commit — permanece na transação do chamador.
        Não gera efeitos financeiros nem auditoria.
        """
        movimento = MovimentoEstoque(**dados.model_dump())
        self.repository.db.add(movimento)

        if flush:
            self.repository.db.flush()

        return movimento

    def criar(self, dados: MovimentoEstoqueCreate) -> MovimentoEstoque:
        """
        Cria e confirma (commit) um novo movimento de estoque.

        Equivale a registrar() seguido de commit — usado pelo CRUD da API.
        """
        movimento = self.registrar(dados)
        self.repository.db.commit()
        self.repository.db.refresh(movimento)
        return movimento

    def listar(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[MovimentoEstoque]:
        """Lista movimentos ativos com paginação."""
        return self.repository.listar(skip=skip, limit=limit)

    def buscar_por_id(self, movimento_id: int) -> MovimentoEstoque:
        """Retorna movimento ativo por id ou levanta exceção."""
        movimento = self.repository.buscar_por_id(movimento_id)

        if movimento is None:
            raise MovimentoEstoqueNaoEncontrado(
                "Movimento de estoque não encontrado."
            )

        return movimento

    def atualizar(
        self,
        movimento_id: int,
        dados: MovimentoEstoqueUpdate,
    ) -> MovimentoEstoque:
        """Atualiza campos informados do movimento (exclude_unset)."""
        movimento = self.buscar_por_id(movimento_id)
        campos: dict[str, Any] = dados.model_dump(exclude_unset=True)

        for campo, valor in campos.items():
            setattr(movimento, campo, valor)

        return self.repository.atualizar(movimento)

    def excluir(self, movimento_id: int) -> MovimentoEstoque:
        """Realiza exclusão lógica do movimento (ativo = False)."""
        movimento = self.buscar_por_id(movimento_id)
        return self.repository.inativar(movimento)

    def saldo_produto(self, produto_id: int) -> Decimal:
        """
        Calcula o saldo de estoque do produto.

        saldo = entradas - saídas
        """
        movimentos = self.repository.listar_por_produto(produto_id)

        saldo = Decimal("0")

        for movimento in movimentos:
            if movimento.tipo == TipoMovimentoEstoque.ENTRADA:
                saldo += Decimal(str(movimento.quantidade))
            elif movimento.tipo == TipoMovimentoEstoque.SAIDA:
                saldo -= Decimal(str(movimento.quantidade))

        return saldo
