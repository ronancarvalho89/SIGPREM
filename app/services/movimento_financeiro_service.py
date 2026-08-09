"""
Service de Movimento Financeiro — regras de negócio (EPIC 001).

Não lança HTTPException. Exceções de domínio são mapeadas na API.
No futuro existirá um middleware/handler global de exceções.
"""

from datetime import date
from decimal import Decimal
from typing import Any
from typing import Optional

from app.models.movimento_financeiro import MovimentoFinanceiro
from app.models.movimento_financeiro import TipoMovimentoFinanceiro
from app.repositories.auditoria_repository import AuditoriaRepository
from app.repositories.movimento_financeiro_repository import (
    MovimentoFinanceiroRepository,
)
from app.schemas.auditoria import AuditoriaCreate
from app.schemas.movimento_financeiro import MovimentoFinanceiroCreate
from app.schemas.movimento_financeiro import MovimentoFinanceiroUpdate
from app.services.auditoria_service import AuditoriaService


class MovimentoFinanceiroNaoEncontrado(Exception):
    """Movimento financeiro ativo não encontrado."""


class MovimentoFinanceiroService:
    """Regras de negócio do cadastro de movimentos financeiros."""

    _TIPOS_ENTRADA = frozenset({TipoMovimentoFinanceiro.VENDA})
    _TIPOS_SAIDA = frozenset(
        {
            TipoMovimentoFinanceiro.COMPRA_CONCRETO,
            TipoMovimentoFinanceiro.PRODUCAO,
        }
    )

    def __init__(self, repository: MovimentoFinanceiroRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository
        self._auditoria_service: Optional[AuditoriaService] = None

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

    def criar(
        self,
        dados: MovimentoFinanceiroCreate,
    ) -> MovimentoFinanceiro:
        """Cria um novo movimento financeiro."""
        movimento = MovimentoFinanceiro(**dados.model_dump())
        movimento = self.repository.criar(movimento)
        self._registrar_auditoria(
            acao="criar",
            entidade_id=movimento.id,
            descricao=(
                f"Movimento financeiro {movimento.id} criado. "
                f"Tipo {movimento.tipo.value}."
            ),
        )
        return movimento

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
        Não gera auditoria aqui para não interromper a transação.
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
        movimento = self.repository.inativar(movimento)
        self._registrar_auditoria(
            acao="inativar",
            entidade_id=movimento.id,
            descricao=f"Movimento financeiro {movimento.id} inativado.",
        )
        return movimento

    def fluxo_caixa(self) -> dict[str, Any]:
        """
        Consolida o fluxo de caixa a partir dos movimentos ativos.

        Retorna totais de entradas, saídas, saldo, quantidade de
        lançamentos e total por tipo. Não persiste dados.
        """
        movimentos = self.repository.listar_ativos()
        return self._consolidar_fluxo(movimentos)

    def fluxo_caixa_periodo(
        self,
        data_inicial: date,
        data_final: date,
    ) -> dict[str, Any]:
        """
        Consolida o fluxo de caixa apenas com movimentos do período.

        Retorna a mesma estrutura de fluxo_caixa().
        """
        movimentos = self.repository.listar_ativos_por_periodo(
            data_inicial=data_inicial,
            data_final=data_final,
        )
        return self._consolidar_fluxo(movimentos)

    def _consolidar_fluxo(
        self,
        movimentos: list[MovimentoFinanceiro],
    ) -> dict[str, Any]:
        """Consolida entradas, saídas, saldo e totais por tipo."""
        total_entradas = Decimal("0")
        total_saidas = Decimal("0")
        total_por_tipo: dict[str, Decimal] = {
            tipo.value: Decimal("0") for tipo in TipoMovimentoFinanceiro
        }

        for movimento in movimentos:
            valor = Decimal(str(movimento.valor))
            tipo = movimento.tipo
            total_por_tipo[tipo.value] += valor

            if tipo in self._TIPOS_ENTRADA:
                total_entradas += valor
            elif tipo in self._TIPOS_SAIDA:
                total_saidas += valor

        return {
            "total_entradas": total_entradas,
            "total_saidas": total_saidas,
            "saldo": total_entradas - total_saidas,
            "quantidade_lancamentos": len(movimentos),
            "total_por_tipo": total_por_tipo,
        }

    def _registrar_auditoria(
        self,
        acao: str,
        entidade_id: int,
        descricao: str,
        usuario_id: Optional[int] = None,
    ) -> None:
        """Registra auditoria financeira via AuditoriaService."""
        try:
            self.auditoria_service.registrar(
                AuditoriaCreate(
                    usuario_id=usuario_id,
                    modulo="financeiro",
                    acao=acao,
                    entidade="MovimentoFinanceiro",
                    entidade_id=entidade_id,
                    descricao=descricao,
                )
            )
        except Exception:
            return
