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


class CompraConcretoService:
    """Regras de negócio do cadastro de compras de concreto."""

    def __init__(self, repository: CompraConcretoRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository
        self.financeiro_service = MovimentoFinanceiroService(
            MovimentoFinanceiroRepository(repository.db)
        )

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
        """Atualiza campos informados da compra (exclude_unset)."""
        compra = self.buscar_por_id(compra_id)
        campos: dict[str, Any] = dados.model_dump(exclude_unset=True)

        if "nota_fiscal" in campos:
            self._validar_nota_fiscal_unica(
                campos["nota_fiscal"],
                compra_id=compra_id,
            )

        for campo, valor in campos.items():
            setattr(compra, campo, valor)

        return self.repository.atualizar(compra)

    def excluir(self, compra_id: int) -> CompraConcreto:
        """Realiza exclusão lógica da compra (ativo = False)."""
        compra = self.buscar_por_id(compra_id)
        return self.repository.inativar(compra)

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
