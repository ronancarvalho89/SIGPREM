"""
Service de Movimento Financeiro — regras de negócio (COMMIT 0035).

Não lança HTTPException. Exceções de domínio são mapeadas na API.
No futuro existirá um middleware/handler global de exceções.
"""

from datetime import date
from decimal import Decimal
from typing import Any

from app.models.movimento_financeiro import MovimentoFinanceiro
from app.models.movimento_financeiro import TipoMovimentoFinanceiro
from app.repositories.movimento_financeiro_repository import (
    MovimentoFinanceiroRepository,
)
from app.schemas.movimento_financeiro import MovimentoFinanceiroCreate
from app.schemas.movimento_financeiro import MovimentoFinanceiroUpdate


class MovimentoFinanceiroNaoEncontrado(Exception):
    """Movimento financeiro ativo não encontrado."""


class MovimentoFinanceiroService:
    """Regras de negócio do cadastro de movimentos financeiros."""

    def __init__(self, repository: MovimentoFinanceiroRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository

    def criar(
        self,
        dados: MovimentoFinanceiroCreate,
    ) -> MovimentoFinanceiro:
        """Cria um novo movimento financeiro."""
        movimento = MovimentoFinanceiro(**dados.model_dump())
        return self.repository.criar(movimento)

    def registrar(
        self,
        tipo: TipoMovimentoFinanceiro,
        data: date,
        valor: Decimal,
        observacao: str = "",
        descricao: str = "",
    ) -> MovimentoFinanceiro:
        """
        Registra um lançamento financeiro na sessão atual.

        Não realiza commit — permanece na transação do chamador.
        """
        movimento = MovimentoFinanceiro(
            tipo=tipo,
            data_movimento=data,
            valor=valor,
            descricao=descricao,
            observacao=observacao,
        )
        self.repository.db.add(movimento)
        return movimento

    def listar(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[MovimentoFinanceiro]:
        """Lista movimentos ativos com paginação."""
        return self.repository.listar(skip=skip, limit=limit)

    def buscar_por_id(self, movimento_id: int) -> MovimentoFinanceiro:
        """Retorna movimento ativo por id ou levanta exceção."""
        movimento = self.repository.buscar_por_id(movimento_id)

        if movimento is None:
            raise MovimentoFinanceiroNaoEncontrado(
                "Movimento financeiro não encontrado."
            )

        return movimento

    def atualizar(
        self,
        movimento_id: int,
        dados: MovimentoFinanceiroUpdate,
    ) -> MovimentoFinanceiro:
        """Atualiza campos informados do movimento (exclude_unset)."""
        movimento = self.buscar_por_id(movimento_id)
        campos: dict[str, Any] = dados.model_dump(exclude_unset=True)

        for campo, valor in campos.items():
            setattr(movimento, campo, valor)

        return self.repository.atualizar(movimento)

    def excluir(self, movimento_id: int) -> MovimentoFinanceiro:
        """Realiza exclusão lógica do movimento (ativo = False)."""
        movimento = self.buscar_por_id(movimento_id)
        return self.repository.excluir(movimento)
