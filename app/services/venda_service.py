"""
Service de Venda — regras de negócio (EPIC 001).

Não lança HTTPException. Exceções de domínio são mapeadas na API.
No futuro existirá um middleware/handler global de exceções.
"""

from datetime import date
from decimal import Decimal
from typing import Any
from typing import Optional
from uuid import UUID

from app.models.item_venda import ItemVenda
from app.models.movimento_estoque import TipoMovimentoEstoque
from app.models.movimento_financeiro import TipoMovimentoFinanceiro
from app.models.venda import Venda
from app.repositories.auditoria_repository import AuditoriaRepository
from app.repositories.movimento_estoque_repository import (
    MovimentoEstoqueRepository,
)
from app.repositories.movimento_financeiro_repository import (
    MovimentoFinanceiroRepository,
)
from app.repositories.venda_repository import VendaRepository
from app.schemas.auditoria import AuditoriaCreate
from app.schemas.movimento_estoque import MovimentoEstoqueCreate
from app.schemas.venda import VendaCreate
from app.schemas.venda import VendaUpdate
from app.services.auditoria_service import AuditoriaService
from app.services.movimento_estoque_service import MovimentoEstoqueService
from app.services.movimento_financeiro_service import MovimentoFinanceiroService


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


class VendaJaEfetivada(Exception):
    """
    Venda com efeitos aplicados não pode ser alterada nem inativada.

    Efeitos (itens, estoque, financeiro) ocorrem na criação.
    Cancelamento/estorno fica para operação específica futura.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


_MSG_VENDA_EFETIVADA = (
    "Venda efetivada não pode ser alterada nem inativada. "
    "Utilize futuramente a operação de cancelamento/estorno."
)


class VendaService:
    """Regras de negócio do cadastro de vendas."""

    def __init__(self, repository: VendaRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository
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
        dados: VendaCreate,
        itens: Optional[list[Any]] = None,
        usuario_id: Optional[int] = None,
    ) -> Venda:
        """
        Cria venda, ItemVenda, baixa de estoque e MovimentoFinanceiro
        na mesma transação.
        """
        self._validar_numero_unico(dados.numero)

        itens_venda = self._resolver_itens(dados, itens)

        venda = Venda(**dados.model_dump(exclude={"itens"}))

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

            self.financeiro_service.registrar(
                tipo=TipoMovimentoFinanceiro.VENDA,
                data=venda.data_venda,
                valor=venda.valor_total,
                descricao="Venda",
                observacao=(
                    f"Cliente ID {venda.cliente_id}. "
                    f"Venda ID {venda.id}."
                ),
            )

            venda = self.repository.criar(venda)
            self._registrar_auditoria(
                acao="criar",
                entidade_id=venda.id,
                descricao=(
                    f"Venda {venda.id} criada. "
                    f"Número {venda.numero}."
                ),
                usuario_id=usuario_id,
            )
            return venda

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

    def atualizar(
        self,
        venda_id: UUID,
        dados: VendaUpdate,
        usuario_id: Optional[int] = None,
    ) -> Venda:
        """
        Bloqueado para venda efetivada (Pacote 4.6.1).

        Qualquer venda ativa já possui efeitos de itens, estoque e
        financeiro aplicados na criação.
        """
        _ = dados, usuario_id
        venda = self.buscar_por_id(venda_id)
        self._garantir_nao_efetivada(venda)

    def excluir(
        self,
        venda_id: UUID,
        usuario_id: Optional[int] = None,
    ) -> Venda:
        """
        Bloqueado para venda efetivada (Pacote 4.6.1).

        Soft delete sem estorno deixaria estoque e financeiro
        inconsistentes.
        """
        _ = usuario_id
        venda = self.buscar_por_id(venda_id)
        self._garantir_nao_efetivada(venda)

    def relatorio_periodo(
        self,
        data_inicial: date,
        data_final: date,
    ) -> dict[str, Any]:
        """
        Consolida relatório gerencial de vendas no período informado.
        """
        vendas = self.repository.listar_ativas_por_periodo(
            data_inicial=data_inicial,
            data_final=data_final,
        )
        return self._consolidar_relatorio(vendas)

    def _consolidar_relatorio(
        self,
        vendas: list[Venda],
    ) -> dict[str, Any]:
        """Consolida indicadores gerenciais a partir de uma lista de vendas."""
        quantidade_vendas = len(vendas)

        if quantidade_vendas == 0:
            zero = Decimal("0")
            return {
                "quantidade_vendas": 0,
                "valor_total": zero,
                "ticket_medio": zero,
                "maior_venda": zero,
                "menor_venda": zero,
                "clientes_atendidos": 0,
            }

        valores = [Decimal(str(venda.valor_total)) for venda in vendas]
        valor_total = sum(valores, Decimal("0"))
        ticket_medio = valor_total / Decimal(quantidade_vendas)
        clientes_atendidos = len({venda.cliente_id for venda in vendas})

        return {
            "quantidade_vendas": quantidade_vendas,
            "valor_total": valor_total,
            "ticket_medio": ticket_medio,
            "maior_venda": max(valores),
            "menor_venda": min(valores),
            "clientes_atendidos": clientes_atendidos,
        }

    def _garantir_nao_efetivada(self, venda: Venda) -> None:
        """
        Impede update/delete de venda efetivada.

        Venda ativa encontrada por buscar_por_id já passou pela criação
        completa (itens + estoque + financeiro). Sem campo 'efetivado',
        a existência ativa é o sinal de efetivação.
        """
        _ = venda
        raise VendaJaEfetivada(_MSG_VENDA_EFETIVADA)

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

            self.estoque_service.registrar(
                MovimentoEstoqueCreate(
                    data=venda.data_venda,
                    produto_id=item.produto_id,
                    quantidade=item.quantidade,
                    tipo=TipoMovimentoEstoque.SAIDA,
                    observacao=f"Venda {venda.numero}",
                )
            )

            reservado[item.produto_id] = (
                reservado.get(item.produto_id, Decimal("0"))
                + Decimal(str(item.quantidade))
            )

    def _registrar_auditoria(
        self,
        acao: str,
        entidade_id: UUID,
        descricao: str,
        usuario_id: Optional[int] = None,
    ) -> None:
        """
        Registra auditoria da operação de venda via AuditoriaService.

        entidade_id permanece Integer no schema atual — UUID é truncado
        para o campo numérico; o UUID completo fica na descricao.
        Alterar o tipo exige migration futura (sem Alembic neste pacote).

        Falha de auditoria não interrompe a operação comercial; sem
        infraestrutura de logs no projeto, a falha permanece engolida.
        """
        try:
            self.auditoria_service.registrar(
                AuditoriaCreate(
                    usuario_id=usuario_id,
                    modulo="venda",
                    acao=acao,
                    entidade="Venda",
                    # Truncamento legado até migration de entidade_id → string.
                    entidade_id=int(entidade_id.int % (2**31 - 1)),
                    descricao=descricao,
                )
            )
        except Exception:
            return
