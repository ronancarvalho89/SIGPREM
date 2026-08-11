"""
Service de Produção — regras de negócio (EPIC 001).

Não lança HTTPException. Exceções de domínio são mapeadas na API.
No futuro existirá um middleware/handler global de exceções.
"""

from datetime import date
from decimal import Decimal
from typing import Any
from typing import Optional

from app.models.compra_concreto import CompraConcreto
from app.models.movimento_estoque import TipoMovimentoEstoque
from app.models.movimento_financeiro import TipoMovimentoFinanceiro
from app.models.produto import Produto
from app.models.producao import Producao
from app.repositories.auditoria_repository import AuditoriaRepository
from app.repositories.funcionario_valor_produto_repository import (
    FuncionarioValorProdutoRepository,
)
from app.repositories.movimento_estoque_repository import (
    MovimentoEstoqueRepository,
)
from app.repositories.movimento_financeiro_repository import (
    MovimentoFinanceiroRepository,
)
from app.repositories.producao_repository import ProducaoRepository
from app.schemas.auditoria import AuditoriaCreate
from app.schemas.movimento_estoque import MovimentoEstoqueCreate
from app.schemas.producao import ProducaoCreate
from app.schemas.producao import ProducaoUpdate
from app.services.auditoria_service import AuditoriaService
from app.services.movimento_estoque_service import MovimentoEstoqueService
from app.services.movimento_financeiro_service import MovimentoFinanceiroService


class ProducaoNaoEncontrada(Exception):
    """Produção ativa não encontrada."""


class SaldoConcretoInsuficiente(Exception):
    """Saldo de concreto insuficiente para a produção."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ProducaoDadosInvalidos(Exception):
    """Referências inválidas para criação da produção."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ValorMaoObraNaoCadastrado(Exception):
    """Não existe valor de mão de obra para o funcionário/produto."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ProducaoJaEfetivada(Exception):
    """
    Produção com efeitos aplicados não pode ser alterada nem inativada.

    Efeitos (saldo concreto, estoque, financeiro) ocorrem na criação.
    Cancelamento/estorno fica para operação específica futura.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


_MSG_PRODUCAO_EFETIVADA = (
    "Produção efetivada não pode ser alterada nem inativada. "
    "Utilize futuramente a operação de cancelamento/estorno."
)


class ProducaoService:
    """Regras de negócio do cadastro de produção."""

    def __init__(self, repository: ProducaoRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository
        self._valor_repository: Optional[
            FuncionarioValorProdutoRepository
        ] = None
        self._estoque_service: Optional[MovimentoEstoqueService] = None
        self._financeiro_service: Optional[MovimentoFinanceiroService] = None
        self._auditoria_service: Optional[AuditoriaService] = None

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
    def valor_repository(self) -> FuncionarioValorProdutoRepository:
        """Repository de valor mão de obra (lazy)."""
        if self._valor_repository is None:
            self._valor_repository = FuncionarioValorProdutoRepository(
                self.repository.db
            )
        return self._valor_repository

    @valor_repository.setter
    def valor_repository(
        self,
        value: FuncionarioValorProdutoRepository,
    ) -> None:
        """Permite injeção/substituição em testes."""
        self._valor_repository = value

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
        dados: ProducaoCreate,
        usuario_id: Optional[int] = None,
    ) -> Producao:
        """
        Cria produção, consome concreto, calcula mão de obra,
        gera entrada de estoque e custo financeiro na mesma transação.
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

        valor_cadastro = self.valor_repository.buscar_por_funcionario_produto(
            dados.funcionario_id,
            dados.produto_id,
        )

        if valor_cadastro is None:
            raise ValorMaoObraNaoCadastrado(
                "Não existe valor de mão de obra cadastrado "
                "para este funcionário e produto."
            )

        concreto = (
            Decimal(dados.quantidade_produzida)
            * Decimal(produto.concreto_por_unidade)
        )

        if compra.saldo < concreto:
            raise SaldoConcretoInsuficiente(
                "Saldo insuficiente de concreto."
            )

        valor_mao_obra = (
            Decimal(dados.quantidade_produzida)
            * Decimal(valor_cadastro.valor)
        )

        try:
            compra.saldo -= concreto

            producao = Producao(
                data=dados.data,
                funcionario_id=dados.funcionario_id,
                produto_id=dados.produto_id,
                compra_concreto_id=dados.compra_concreto_id,
                quantidade_produzida=dados.quantidade_produzida,
                concreto_consumido=concreto,
                valor_producao=valor_mao_obra,
                observacao=dados.observacao,
            )

            self.repository.db.add(producao)
            self.repository.db.flush()

            self.estoque_service.registrar(
                MovimentoEstoqueCreate(
                    data=producao.data,
                    produto_id=producao.produto_id,
                    quantidade=producao.quantidade_produzida,
                    tipo=TipoMovimentoEstoque.ENTRADA,
                    producao_id=producao.id,
                    observacao="Entrada automática gerada pela produção.",
                )
            )

            # Tipo disponível no model: PRODUCAO (custo de produção / mão de obra).
            # Model sem funcionario_id/producao_id — referências na observação.
            self.financeiro_service.registrar(
                tipo=TipoMovimentoFinanceiro.PRODUCAO,
                data=producao.data,
                valor=producao.valor_producao,
                descricao="Custo de produção",
                observacao=(
                    f"Produção {producao.id}. "
                    f"Funcionário ID {producao.funcionario_id}."
                ),
            )

            producao = self.repository.criar(producao)
            self._registrar_auditoria(
                acao="criar",
                entidade_id=producao.id,
                descricao=f"Produção {producao.id} criada.",
                usuario_id=usuario_id,
            )
            return producao

        except Exception:
            self.repository.db.rollback()
            raise

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
        """
        Bloqueado para produção efetivada (Pacote 4.6.2).

        Qualquer produção ativa já possui efeitos de concreto, estoque
        e financeiro aplicados na criação.
        """
        _ = dados
        producao = self.buscar_por_id(producao_id)
        self._garantir_nao_efetivada(producao)

    def excluir(
        self,
        producao_id: int,
        usuario_id: Optional[int] = None,
    ) -> Producao:
        """
        Bloqueado para produção efetivada (Pacote 4.6.2).

        Soft delete sem estorno deixaria concreto, estoque e financeiro
        inconsistentes.
        """
        _ = usuario_id
        producao = self.buscar_por_id(producao_id)
        self._garantir_nao_efetivada(producao)

    def relatorio_periodo(
        self,
        data_inicial: date,
        data_final: date,
    ) -> dict[str, Any]:
        """
        Consolida relatório gerencial de produção no período informado.
        """
        producoes = self.repository.listar_ativas_por_periodo(
            data_inicial=data_inicial,
            data_final=data_final,
        )
        return self._consolidar_relatorio(producoes)

    def _consolidar_relatorio(
        self,
        producoes: list[Producao],
    ) -> dict[str, Any]:
        """Consolida indicadores gerenciais a partir de uma lista de produções."""
        quantidade_producoes = len(producoes)

        if quantidade_producoes == 0:
            zero = Decimal("0")
            return {
                "quantidade_producoes": 0,
                "quantidade_total_produzida": zero,
                "custo_total_producao": zero,
                "custo_medio_producao": zero,
                "funcionarios_envolvidos": 0,
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
        funcionarios_envolvidos = len(
            {p.funcionario_id for p in producoes}
        )

        return {
            "quantidade_producoes": quantidade_producoes,
            "quantidade_total_produzida": quantidade_total_produzida,
            "custo_total_producao": custo_total_producao,
            "custo_medio_producao": custo_medio_producao,
            "funcionarios_envolvidos": funcionarios_envolvidos,
        }

    def _garantir_nao_efetivada(self, producao: Producao) -> None:
        """
        Impede update/delete de produção efetivada.

        Produção ativa encontrada por buscar_por_id já passou pela
        criação completa (concreto + estoque + financeiro).
        """
        _ = producao
        raise ProducaoJaEfetivada(_MSG_PRODUCAO_EFETIVADA)

    def _registrar_auditoria(
        self,
        acao: str,
        entidade_id: int,
        descricao: str,
        usuario_id: Optional[int] = None,
    ) -> None:
        """
        Registra auditoria da produção via AuditoriaService.

        Falha de auditoria não interrompe a operação; sem logs no
        projeto, a falha permanece engolida neste pacote.
        """
        try:
            self.auditoria_service.registrar(
                AuditoriaCreate(
                    usuario_id=usuario_id,
                    modulo="producao",
                    acao=acao,
                    entidade="Producao",
                    entidade_id=entidade_id,
                    descricao=descricao,
                )
            )
        except Exception:
            return
