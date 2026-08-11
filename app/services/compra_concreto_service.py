"""
Service de Compra de Concreto — regras de negócio (COMMIT 0035).

Não lança HTTPException. Exceções de domínio são mapeadas na API.
No futuro existirá um middleware/handler global de exceções.
"""

from typing import Any
from typing import Optional

from app.models.compra_concreto import CompraConcreto
from app.models.movimento_financeiro import TipoMovimentoFinanceiro
from app.repositories.compra_concreto_repository import CompraConcretoRepository
from app.repositories.movimento_financeiro_repository import (
    MovimentoFinanceiroRepository,
)
from app.schemas.compra_concreto import CompraConcretoCreate
from app.schemas.compra_concreto import CompraConcretoUpdate
from app.services.movimento_financeiro_service import MovimentoFinanceiroService


class CompraConcretoNaoEncontrada(Exception):
    """Compra de concreto ativa não encontrada."""


class CompraConcretoDuplicada(Exception):
    """Compra de concreto com nota fiscal já cadastrada."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class CompraConcretoJaEfetivada(Exception):
    """
    Compra com efeitos aplicados não pode ser alterada nem inativada.

    Efeitos (saldo e financeiro) ocorrem na criação; o saldo pode ter
    sido consumido por Produções. Cancelamento/estorno fica para
    operação específica futura.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


_MSG_COMPRA_EFETIVADA = (
    "Compra de concreto efetivada não pode ser alterada nem inativada. "
    "Utilize futuramente a operação de cancelamento/estorno."
)


class CompraConcretoService:
    """Regras de negócio do cadastro de compras de concreto."""

    def __init__(self, repository: CompraConcretoRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository
        self._financeiro_service: Optional[MovimentoFinanceiroService] = None

    @property
    def financeiro_service(self) -> MovimentoFinanceiroService:
        """Service financeiro (lazy) compartilhando a mesma sessão."""
        if self._financeiro_service is None:
            self._financeiro_service = MovimentoFinanceiroService(
                MovimentoFinanceiroRepository(self.repository.db)
            )
        return self._financeiro_service

    @financeiro_service.setter
    def financeiro_service(self, value: MovimentoFinanceiroService) -> None:
        """Permite injeção/substituição em testes."""
        self._financeiro_service = value

    def criar(self, dados: CompraConcretoCreate) -> CompraConcreto:
        """
        Cria compra e gera MovimentoFinanceiro na mesma transação.
        """
        self._validar_nota_fiscal_unica(dados.nota_fiscal)

        compra = CompraConcreto(
            fornecedor_id=dados.fornecedor_id,
            data_compra=dados.data_compra,
            nota_fiscal=dados.nota_fiscal,
            quantidade_comprada=dados.quantidade_comprada,
            quantidade_recebida=dados.quantidade_recebida,
            saldo=dados.quantidade_recebida,
            valor_total=dados.valor_total,
            observacao=dados.observacao,
        )

        try:
            self.repository.db.add(compra)
            self.repository.db.flush()

            self.financeiro_service.registrar(
                tipo=TipoMovimentoFinanceiro.COMPRA_CONCRETO,
                data=compra.data_compra,
                valor=compra.valor_total,
                descricao="Compra de concreto",
                observacao=(
                    f"Fornecedor ID {compra.fornecedor_id}. "
                    f"Compra ID {compra.id}."
                ),
            )

            return self.repository.criar(compra)

        except Exception:
            self.repository.db.rollback()
            raise

    def listar(self, skip: int = 0, limit: int = 50) -> list[CompraConcreto]:
        """Lista compras ativas com paginação."""
        return self.repository.listar(skip=skip, limit=limit)

    def buscar_por_id(self, compra_id: int) -> CompraConcreto:
        """Retorna compra ativa por id ou levanta CompraConcretoNaoEncontrada."""
        compra = self.repository.buscar_por_id(compra_id)

        if compra is None:
            raise CompraConcretoNaoEncontrada(
                "Compra de concreto não encontrada."
            )

        return compra

    def atualizar(
        self,
        compra_id: int,
        dados: CompraConcretoUpdate,
    ) -> CompraConcreto:
        """
        Bloqueado para compra efetivada (Pacote 4.6.3).

        Qualquer compra ativa já possui saldo e financeiro aplicados
        na criação; o saldo pode ter sido consumido por Produções.
        """
        _ = dados
        compra = self.buscar_por_id(compra_id)
        self._garantir_nao_efetivada(compra)

    def excluir(self, compra_id: int) -> CompraConcreto:
        """
        Bloqueado para compra efetivada (Pacote 4.6.3).

        Soft delete sem estorno deixaria financeiro e saldos
        (e Produções dependentes) inconsistentes.
        """
        compra = self.buscar_por_id(compra_id)
        self._garantir_nao_efetivada(compra)

    def _garantir_nao_efetivada(self, compra: CompraConcreto) -> None:
        """
        Impede update/delete de compra efetivada.

        Compra ativa encontrada por buscar_por_id já passou pela
        criação completa (saldo + financeiro).
        """
        _ = compra
        raise CompraConcretoJaEfetivada(_MSG_COMPRA_EFETIVADA)

    def _validar_nota_fiscal_unica(
        self,
        nota_fiscal: str,
        compra_id: Optional[int] = None,
    ) -> None:
        """Valida nota fiscal duplicada quando informada."""
        if not nota_fiscal:
            return

        existente = self.repository.buscar_por_nota_fiscal(nota_fiscal)

        if existente is not None and existente.id != compra_id:
            raise CompraConcretoDuplicada(
                "Já existe uma compra cadastrada com esta nota fiscal."
            )
