"""
Testes do módulo Vendas (EPIC 003 — ETAPA 6).
"""

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_current_usuario
from app.database.database import get_db
from app.main import app
from app.models.auditoria import Auditoria
from app.models.cliente import Cliente
from app.models.item_venda import ItemVenda
from app.models.movimento_estoque import MovimentoEstoque
from app.models.movimento_estoque import TipoMovimentoEstoque
from app.models.movimento_financeiro import MovimentoFinanceiro
from app.models.movimento_financeiro import TipoMovimentoFinanceiro
from app.models.produto import CategoriaProduto
from app.models.produto import Produto
from app.models.produto import TipoProduto
from app.models.produto import UnidadeProduto
from app.models.usuario import Usuario
from app.models.venda import Venda
from app.repositories.movimento_estoque_repository import (
    MovimentoEstoqueRepository,
)
from app.repositories.venda_repository import VendaRepository
from app.schemas.movimento_estoque import MovimentoEstoqueCreate
from app.schemas.venda import VendaCreate
from app.schemas.venda import VendaUpdate
from app.services.movimento_estoque_service import MovimentoEstoqueService
from app.services.venda_service import EstoqueInsuficiente
from app.services.venda_service import VendaDuplicada
from app.services.venda_service import VendaJaEfetivada
from app.services.venda_service import VendaNaoEncontrada
from app.services.venda_service import VendaService


@pytest.fixture()
def venda_service(db_session: Session) -> VendaService:
    """VendaService na sessão de teste."""
    return VendaService(VendaRepository(db_session))


@pytest.fixture()
def estoque_service(db_session: Session) -> MovimentoEstoqueService:
    """Usado apenas para preparar saldo e ler saldos após a venda."""
    return MovimentoEstoqueService(MovimentoEstoqueRepository(db_session))


@pytest.fixture()
def cenario(
    db_session: Session,
    estoque_service: MovimentoEstoqueService,
) -> dict[str, Any]:
    """Cliente + 2 produtos com estoque inicial (via Service de estoque)."""
    cliente = Cliente(
        razao_social="Cliente Vendas Teste",
        nome_fantasia="Cliente",
        cpf_cnpj="11222333000181",
        telefone="",
        whatsapp="",
        email="",
        observacao="",
    )
    produto_a = Produto(
        codigo="VEN-A",
        descricao="Produto Venda A",
        categoria=CategoriaProduto.BLOQUETE,
        modelo="A",
        unidade=UnidadeProduto.UN,
        concreto_por_unidade=Decimal("0"),
        tipo_produto=TipoProduto.PRE_MOLDADO,
    )
    produto_b = Produto(
        codigo="VEN-B",
        descricao="Produto Venda B",
        categoria=CategoriaProduto.BLOQUETE,
        modelo="B",
        unidade=UnidadeProduto.UN,
        concreto_por_unidade=Decimal("0"),
        tipo_produto=TipoProduto.PRE_MOLDADO,
    )
    db_session.add_all([cliente, produto_a, produto_b])
    db_session.commit()
    db_session.refresh(cliente)
    db_session.refresh(produto_a)
    db_session.refresh(produto_b)

    for produto_id, qtd in (
        (produto_a.id, Decimal("100")),
        (produto_b.id, Decimal("50")),
    ):
        estoque_service.criar(
            MovimentoEstoqueCreate(
                data=date(2026, 8, 1),
                produto_id=produto_id,
                quantidade=qtd,
                tipo=TipoMovimentoEstoque.ENTRADA,
                observacao="saldo inicial vendas",
            )
        )

    return {
        "cliente": cliente,
        "produto_a": produto_a,
        "produto_b": produto_b,
    }


@pytest.fixture()
def client_auth(db_session: Session, usuario: Usuario):
    """TestClient autenticado com a sessão de teste."""

    def _override_db():
        yield db_session

    def _override_usuario():
        return usuario

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_usuario] = _override_usuario
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture()
def client_anon(db_session: Session):
    """TestClient sem autenticação."""

    def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def _venda_create(
    cenario: dict[str, Any],
    *,
    numero: str = "V-001",
    valor_total: Decimal = Decimal("0"),
    itens: list[dict[str, Any]] | None = None,
) -> VendaCreate:
    if itens is None:
        itens = [
            {
                "produto_id": cenario["produto_a"].id,
                "quantidade": Decimal("1"),
                "valor_unitario": Decimal("1.00"),
            }
        ]
    return VendaCreate(
        cliente_id=cenario["cliente"].id,
        data_venda=date(2026, 8, 15),
        numero=numero,
        valor_total=valor_total,
        observacoes="venda teste",
        status="ABERTA",
        itens=itens,
    )


def _itens_financeiros(db_session: Session, venda_id: UUID) -> list[MovimentoFinanceiro]:
    return (
        db_session.query(MovimentoFinanceiro)
        .filter(
            MovimentoFinanceiro.tipo == TipoMovimentoFinanceiro.VENDA,
            MovimentoFinanceiro.observacao.contains(f"Venda ID {venda_id}"),
        )
        .all()
    )


def _saidas_venda(db_session: Session, numero: str) -> list[MovimentoEstoque]:
    return (
        db_session.query(MovimentoEstoque)
        .filter(
            MovimentoEstoque.tipo == TipoMovimentoEstoque.SAIDA,
            MovimentoEstoque.observacao == f"Venda {numero}",
        )
        .all()
    )


# ---------------------------------------------------------------------------
# 2–3. Criação / múltiplos itens
# ---------------------------------------------------------------------------


def test_criar_venda_com_item_efeitos_completos(
    venda_service: VendaService,
    estoque_service: MovimentoEstoqueService,
    cenario: dict[str, Any],
    db_session: Session,
) -> None:
    venda = venda_service.criar(
        _venda_create(cenario, numero="V-010"),
        itens=[
            {
                "produto_id": cenario["produto_a"].id,
                "quantidade": Decimal("10"),
                "valor_unitario": Decimal("25.00"),
            }
        ],
    )

    assert isinstance(venda.id, UUID)
    assert venda.cliente_id == cenario["cliente"].id
    assert Decimal(str(venda.valor_total)) == Decimal("250.00")

    itens = (
        db_session.query(ItemVenda)
        .filter(ItemVenda.venda_id == venda.id)
        .all()
    )
    assert len(itens) == 1
    assert itens[0].produto_id == cenario["produto_a"].id
    assert Decimal(str(itens[0].quantidade)) == Decimal("10")
    assert Decimal(str(itens[0].valor_unitario)) == Decimal("25.00")
    assert Decimal(str(itens[0].valor_total)) == Decimal("250.00")

    saidas = _saidas_venda(db_session, "V-010")
    assert len(saidas) == 1
    assert saidas[0].tipo == TipoMovimentoEstoque.SAIDA
    assert saidas[0].produto_id == cenario["produto_a"].id
    assert Decimal(str(saidas[0].quantidade)) == Decimal("10")
    assert estoque_service.saldo_produto(cenario["produto_a"].id) == Decimal("90")

    financeiros = _itens_financeiros(db_session, venda.id)
    assert len(financeiros) == 1
    assert Decimal(str(financeiros[0].valor)) == Decimal("250.00")
    assert financeiros[0].descricao == "Venda"

    auditorias = (
        db_session.query(Auditoria)
        .filter(
            Auditoria.modulo == "venda",
            Auditoria.acao == "criar",
            Auditoria.entidade == "Venda",
        )
        .all()
    )
    assert len(auditorias) == 1
    assert auditorias[0].usuario_id is None  # chamada direta sem usuário
    assert auditorias[0].entidade_id == int(venda.id.int % (2**31 - 1))
    assert str(venda.id) in auditorias[0].descricao


def test_venda_multiplos_itens_isola_estoques(
    venda_service: VendaService,
    estoque_service: MovimentoEstoqueService,
    cenario: dict[str, Any],
    db_session: Session,
) -> None:
    venda = venda_service.criar(
        _venda_create(cenario, numero="V-020"),
        itens=[
            {
                "produto_id": cenario["produto_a"].id,
                "quantidade": Decimal("20"),
                "valor_unitario": Decimal("10.00"),
            },
            {
                "produto_id": cenario["produto_b"].id,
                "quantidade": Decimal("5"),
                "valor_unitario": Decimal("40.00"),
            },
        ],
    )

    assert Decimal(str(venda.valor_total)) == Decimal("400.00")
    itens = (
        db_session.query(ItemVenda)
        .filter(ItemVenda.venda_id == venda.id)
        .all()
    )
    assert len(itens) == 2
    assert estoque_service.saldo_produto(cenario["produto_a"].id) == Decimal("80")
    assert estoque_service.saldo_produto(cenario["produto_b"].id) == Decimal("45")
    assert len(_saidas_venda(db_session, "V-020")) == 2


# ---------------------------------------------------------------------------
# 5. Estoque insuficiente
# ---------------------------------------------------------------------------


def test_estoque_insuficiente_nao_persiste_efeitos(
    venda_service: VendaService,
    estoque_service: MovimentoEstoqueService,
    cenario: dict[str, Any],
    db_session: Session,
) -> None:
    with pytest.raises(EstoqueInsuficiente):
        venda_service.criar(
            _venda_create(cenario, numero="V-030"),
            itens=[
                {
                    "produto_id": cenario["produto_a"].id,
                    "quantidade": Decimal("101"),
                    "valor_unitario": Decimal("1.00"),
                }
            ],
        )

    assert db_session.query(Venda).count() == 0
    assert db_session.query(ItemVenda).count() == 0
    assert len(_saidas_venda(db_session, "V-030")) == 0
    assert (
        db_session.query(MovimentoFinanceiro)
        .filter(MovimentoFinanceiro.tipo == TipoMovimentoFinanceiro.VENDA)
        .count()
        == 0
    )
    assert estoque_service.saldo_produto(cenario["produto_a"].id) == Decimal("100")


# ---------------------------------------------------------------------------
# 9. Rollback financeiro
# ---------------------------------------------------------------------------


def test_rollback_quando_financeiro_falha(
    venda_service: VendaService,
    estoque_service: MovimentoEstoqueService,
    cenario: dict[str, Any],
    db_session: Session,
) -> None:
    class FinanceiroQueFalha:
        def registrar(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("falha financeira na venda")

    venda_service.financeiro_service = FinanceiroQueFalha()  # type: ignore[assignment]

    with pytest.raises(RuntimeError, match="falha financeira"):
        venda_service.criar(
            _venda_create(cenario, numero="V-040"),
            itens=[
                {
                    "produto_id": cenario["produto_a"].id,
                    "quantidade": Decimal("2"),
                    "valor_unitario": Decimal("10.00"),
                }
            ],
        )

    assert db_session.query(Venda).count() == 0
    assert db_session.query(ItemVenda).count() == 0
    assert len(_saidas_venda(db_session, "V-040")) == 0
    assert estoque_service.saldo_produto(cenario["produto_a"].id) == Decimal("100")
    assert (
        db_session.query(Auditoria)
        .filter(Auditoria.modulo == "venda", Auditoria.acao == "criar")
        .count()
        == 0
    )


def test_numero_duplicado(
    venda_service: VendaService,
    cenario: dict[str, Any],
) -> None:
    venda_service.criar(
        _venda_create(cenario, numero="V-DUP"),
        itens=[
            {
                "produto_id": cenario["produto_a"].id,
                "quantidade": Decimal("1"),
                "valor_unitario": Decimal("5.00"),
            }
        ],
    )
    with pytest.raises(VendaDuplicada):
        venda_service.criar(
            _venda_create(cenario, numero="V-DUP"),
            itens=[
                {
                    "produto_id": cenario["produto_a"].id,
                    "quantidade": Decimal("1"),
                    "valor_unitario": Decimal("5.00"),
                }
            ],
        )


# ---------------------------------------------------------------------------
# 10–11. Update / exclusão — Política A (Pacote 4.6.1)
# ---------------------------------------------------------------------------


def test_atualizar_venda_efetivada_bloqueado(
    venda_service: VendaService,
    estoque_service: MovimentoEstoqueService,
    cenario: dict[str, Any],
    db_session: Session,
) -> None:
    venda = venda_service.criar(
        _venda_create(cenario, numero="V-050"),
        itens=[
            {
                "produto_id": cenario["produto_a"].id,
                "quantidade": Decimal("10"),
                "valor_unitario": Decimal("8.00"),
            }
        ],
    )
    saldo_antes = estoque_service.saldo_produto(cenario["produto_a"].id)
    valor_fin = Decimal(str(_itens_financeiros(db_session, venda.id)[0].valor))
    total_antes = Decimal(str(venda.valor_total))
    status_antes = venda.status
    observacoes_antes = venda.observacoes
    mov_estoque_antes = db_session.query(MovimentoEstoque).count()
    mov_fin_antes = db_session.query(MovimentoFinanceiro).count()
    aud_antes = db_session.query(Auditoria).count()

    with pytest.raises(VendaJaEfetivada):
        venda_service.atualizar(
            venda.id,
            VendaUpdate(
                observacoes="atualizada",
                valor_total=Decimal("999.00"),
                status="FECHADA",
            ),
        )

    db_session.refresh(venda)
    assert venda.ativo is True
    assert Decimal(str(venda.valor_total)) == total_antes
    assert venda.status == status_antes
    assert venda.observacoes == observacoes_antes
    assert estoque_service.saldo_produto(cenario["produto_a"].id) == saldo_antes
    assert Decimal(
        str(_itens_financeiros(db_session, venda.id)[0].valor)
    ) == valor_fin
    assert (
        db_session.query(ItemVenda)
        .filter(ItemVenda.venda_id == venda.id)
        .count()
        == 1
    )
    assert db_session.query(MovimentoEstoque).count() == mov_estoque_antes
    assert db_session.query(MovimentoFinanceiro).count() == mov_fin_antes
    assert db_session.query(Auditoria).count() == aud_antes
    assert (
        db_session.query(Auditoria)
        .filter(Auditoria.acao == "atualizar", Auditoria.modulo == "venda")
        .count()
        == 0
    )


def test_excluir_venda_efetivada_bloqueado(
    venda_service: VendaService,
    estoque_service: MovimentoEstoqueService,
    cenario: dict[str, Any],
    db_session: Session,
) -> None:
    venda = venda_service.criar(
        _venda_create(cenario, numero="V-060"),
        itens=[
            {
                "produto_id": cenario["produto_a"].id,
                "quantidade": Decimal("4"),
                "valor_unitario": Decimal("12.00"),
            }
        ],
    )
    saldo_apos_venda = estoque_service.saldo_produto(cenario["produto_a"].id)
    mov_estoque_antes = db_session.query(MovimentoEstoque).count()
    mov_fin_antes = db_session.query(MovimentoFinanceiro).count()
    aud_antes = db_session.query(Auditoria).count()

    with pytest.raises(VendaJaEfetivada):
        venda_service.excluir(venda.id)

    db_session.refresh(venda)
    assert venda.ativo is True
    assert venda_service.buscar_por_id(venda.id).id == venda.id
    assert estoque_service.saldo_produto(cenario["produto_a"].id) == saldo_apos_venda
    assert len(_itens_financeiros(db_session, venda.id)) == 1
    assert (
        db_session.query(ItemVenda)
        .filter(ItemVenda.venda_id == venda.id)
        .count()
        == 1
    )
    assert db_session.query(MovimentoEstoque).count() == mov_estoque_antes
    assert db_session.query(MovimentoFinanceiro).count() == mov_fin_antes
    assert db_session.query(Auditoria).count() == aud_antes
    assert (
        db_session.query(Auditoria)
        .filter(Auditoria.acao == "inativar", Auditoria.modulo == "venda")
        .count()
        == 0
    )


# ---------------------------------------------------------------------------
# 14. Relatório
# ---------------------------------------------------------------------------


def test_relatorio_periodo(
    venda_service: VendaService,
    cenario: dict[str, Any],
) -> None:
    vazio = venda_service.relatorio_periodo(date(2026, 7, 1), date(2026, 7, 31))
    assert vazio["quantidade_vendas"] == 0
    assert vazio["valor_total"] == Decimal("0")

    venda_service.criar(
        _venda_create(cenario, numero="V-070"),
        itens=[
            {
                "produto_id": cenario["produto_a"].id,
                "quantidade": Decimal("2"),
                "valor_unitario": Decimal("50.00"),
            }
        ],
    )
    venda_service.criar(
        _venda_create(cenario, numero="V-071"),
        itens=[
            {
                "produto_id": cenario["produto_b"].id,
                "quantidade": Decimal("1"),
                "valor_unitario": Decimal("20.00"),
            }
        ],
    )

    relatorio = venda_service.relatorio_periodo(
        date(2026, 8, 1),
        date(2026, 8, 31),
    )
    assert relatorio["quantidade_vendas"] == 2
    assert relatorio["valor_total"] == Decimal("120.00")
    assert relatorio["clientes_atendidos"] == 1
    assert relatorio["maior_venda"] == Decimal("100.00")
    assert relatorio["menor_venda"] == Decimal("20.00")


# ---------------------------------------------------------------------------
# 13. API — fluxo completo (EPIC 004 / 4.2)
# ---------------------------------------------------------------------------


def test_api_vendas_exige_autenticacao(client_anon: TestClient) -> None:
    assert client_anon.get("/vendas").status_code == 401
    assert client_anon.get("/itens-venda").status_code == 401


def test_api_post_venda_com_um_item_fluxo_completo(
    client_auth: TestClient,
    estoque_service: MovimentoEstoqueService,
    cenario: dict[str, Any],
    db_session: Session,
) -> None:
    criar = client_auth.post(
        "/vendas",
        json={
            "cliente_id": cenario["cliente"].id,
            "data_venda": "2026-08-15",
            "numero": "V-API-1",
            "valor_total": "999.00",
            "observacoes": "api um item",
            "status": "ABERTA",
            "itens": [
                {
                    "produto_id": cenario["produto_a"].id,
                    "quantidade": "10",
                    "valor_unitario": "15.00",
                }
            ],
        },
    )
    assert criar.status_code == 201
    body = criar.json()
    venda_id = UUID(body["id"])
    assert Decimal(str(body["valor_total"])) == Decimal("150.00")

    itens = (
        db_session.query(ItemVenda)
        .filter(ItemVenda.venda_id == venda_id)
        .all()
    )
    assert len(itens) == 1
    assert Decimal(str(itens[0].quantidade)) == Decimal("10")

    assert len(_saidas_venda(db_session, "V-API-1")) == 1
    assert estoque_service.saldo_produto(cenario["produto_a"].id) == Decimal(
        "90"
    )

    financeiros = _itens_financeiros(db_session, venda_id)
    assert len(financeiros) == 1
    assert Decimal(str(financeiros[0].valor)) == Decimal("150.00")

    assert (
        db_session.query(Auditoria)
        .filter(Auditoria.modulo == "venda", Auditoria.acao == "criar")
        .count()
        == 1
    )


def test_api_auditoria_recebe_usuario_id(
    client_auth: TestClient,
    cenario: dict[str, Any],
    db_session: Session,
    usuario: Usuario,
) -> None:
    criar = client_auth.post(
        "/vendas",
        json={
            "cliente_id": cenario["cliente"].id,
            "data_venda": "2026-08-15",
            "numero": "V-API-AUD",
            "itens": [
                {
                    "produto_id": cenario["produto_a"].id,
                    "quantidade": "1",
                    "valor_unitario": "10.00",
                }
            ],
        },
    )
    assert criar.status_code == 201
    venda_id = UUID(criar.json()["id"])

    auditoria = (
        db_session.query(Auditoria)
        .filter(Auditoria.modulo == "venda", Auditoria.acao == "criar")
        .one()
    )
    assert auditoria.usuario_id == usuario.id
    assert str(venda_id) in auditoria.descricao


def test_api_post_venda_multiplos_itens(
    client_auth: TestClient,
    estoque_service: MovimentoEstoqueService,
    cenario: dict[str, Any],
    db_session: Session,
) -> None:
    criar = client_auth.post(
        "/vendas",
        json={
            "cliente_id": cenario["cliente"].id,
            "data_venda": "2026-08-15",
            "numero": "V-API-2",
            "observacoes": "",
            "status": "ABERTA",
            "itens": [
                {
                    "produto_id": cenario["produto_a"].id,
                    "quantidade": "5",
                    "valor_unitario": "10.00",
                },
                {
                    "produto_id": cenario["produto_b"].id,
                    "quantidade": "2",
                    "valor_unitario": "20.00",
                },
            ],
        },
    )
    assert criar.status_code == 201
    assert Decimal(str(criar.json()["valor_total"])) == Decimal("90.00")
    assert estoque_service.saldo_produto(cenario["produto_a"].id) == Decimal(
        "95"
    )
    assert estoque_service.saldo_produto(cenario["produto_b"].id) == Decimal(
        "48"
    )
    assert len(_saidas_venda(db_session, "V-API-2")) == 2


def test_api_post_venda_sem_itens_rejeitada(
    client_auth: TestClient,
    cenario: dict[str, Any],
) -> None:
    response = client_auth.post(
        "/vendas",
        json={
            "cliente_id": cenario["cliente"].id,
            "data_venda": "2026-08-15",
            "numero": "V-API-VAZIA",
            "itens": [],
        },
    )
    assert response.status_code == 422


def test_api_estoque_insuficiente_retorna_400(
    client_auth: TestClient,
    cenario: dict[str, Any],
    db_session: Session,
) -> None:
    response = client_auth.post(
        "/vendas",
        json={
            "cliente_id": cenario["cliente"].id,
            "data_venda": "2026-08-15",
            "numero": "V-API-EST",
            "itens": [
                {
                    "produto_id": cenario["produto_a"].id,
                    "quantidade": "999",
                    "valor_unitario": "1.00",
                }
            ],
        },
    )
    assert response.status_code == 400
    assert "Estoque insuficiente" in response.json()["detail"]
    assert db_session.query(Venda).count() == 0
    assert db_session.query(ItemVenda).count() == 0


def test_api_erro_inesperado_nao_mascarado_como_400(
    client_auth: TestClient,
    cenario: dict[str, Any],
) -> None:
    """Erros internos não devem ser convertidos em HTTP 400."""
    original = VendaService.criar

    def _falha(self, *args, **kwargs):
        raise RuntimeError("falha interna venda")

    VendaService.criar = _falha  # type: ignore[method-assign]
    try:
        with pytest.raises(RuntimeError, match="falha interna venda"):
            client_auth.post(
                "/vendas",
                json={
                    "cliente_id": cenario["cliente"].id,
                    "data_venda": "2026-08-15",
                    "numero": "V-API-500",
                    "itens": [
                        {
                            "produto_id": cenario["produto_a"].id,
                            "quantidade": "1",
                            "valor_unitario": "10.00",
                        }
                    ],
                },
            )
    finally:
        VendaService.criar = original  # type: ignore[method-assign]


def test_api_rollback_quando_financeiro_falha(
    client_auth: TestClient,
    cenario: dict[str, Any],
    db_session: Session,
    estoque_service: MovimentoEstoqueService,
) -> None:
    from app.services.movimento_financeiro_service import (
        MovimentoFinanceiroService,
    )

    original = MovimentoFinanceiroService.registrar

    def _falha(self, *args, **kwargs):
        raise RuntimeError("falha financeira api")

    MovimentoFinanceiroService.registrar = _falha  # type: ignore[method-assign]
    try:
        with pytest.raises(RuntimeError, match="falha financeira api"):
            client_auth.post(
                "/vendas",
                json={
                    "cliente_id": cenario["cliente"].id,
                    "data_venda": "2026-08-15",
                    "numero": "V-API-ROLL",
                    "itens": [
                        {
                            "produto_id": cenario["produto_a"].id,
                            "quantidade": "2",
                            "valor_unitario": "10.00",
                        }
                    ],
                },
            )
    finally:
        MovimentoFinanceiroService.registrar = original  # type: ignore[method-assign]

    assert db_session.query(Venda).count() == 0
    assert db_session.query(ItemVenda).count() == 0
    assert len(_saidas_venda(db_session, "V-API-ROLL")) == 0
    assert (
        db_session.query(MovimentoFinanceiro)
        .filter(MovimentoFinanceiro.tipo == TipoMovimentoFinanceiro.VENDA)
        .count()
        == 0
    )
    assert estoque_service.saldo_produto(cenario["produto_a"].id) == Decimal(
        "100"
    )


def test_api_criar_listar_relatorio_update_delete_bloqueados(
    client_auth: TestClient,
    cenario: dict[str, Any],
    db_session: Session,
    estoque_service: MovimentoEstoqueService,
) -> None:
    criar = client_auth.post(
        "/vendas",
        json={
            "cliente_id": cenario["cliente"].id,
            "data_venda": "2026-08-15",
            "numero": "V-API-CRUD",
            "observacoes": "api",
            "status": "ABERTA",
            "itens": [
                {
                    "produto_id": cenario["produto_a"].id,
                    "quantidade": "1",
                    "valor_unitario": "50.00",
                }
            ],
        },
    )
    assert criar.status_code == 201
    venda_id = criar.json()["id"]
    assert Decimal(str(criar.json()["valor_total"])) == Decimal("50.00")

    assert client_auth.get("/vendas").status_code == 200
    assert len(client_auth.get("/vendas").json()) == 1
    assert client_auth.get(f"/vendas/{venda_id}").status_code == 200

    relatorio = client_auth.get(
        "/vendas/relatorio/periodo",
        params={
            "data_inicial": "2026-08-01",
            "data_final": "2026-08-31",
        },
    )
    assert relatorio.status_code == 200
    assert relatorio.json()["quantidade_vendas"] == 1

    saldo_antes = estoque_service.saldo_produto(cenario["produto_a"].id)
    fin_antes = len(_itens_financeiros(db_session, UUID(venda_id)))

    atualizar = client_auth.put(
        f"/vendas/{venda_id}",
        json={"observacoes": "api atualizada"},
    )
    assert atualizar.status_code == 400
    assert "efetivada" in atualizar.json()["detail"].lower()

    excluir = client_auth.delete(f"/vendas/{venda_id}")
    assert excluir.status_code == 400
    assert "efetivada" in excluir.json()["detail"].lower()

    detalhe = client_auth.get(f"/vendas/{venda_id}")
    assert detalhe.status_code == 200
    assert detalhe.json()["ativo"] is True
    assert detalhe.json()["observacoes"] == "api"
    assert estoque_service.saldo_produto(cenario["produto_a"].id) == saldo_antes
    assert len(_itens_financeiros(db_session, UUID(venda_id))) == fin_antes
    assert (
        db_session.query(ItemVenda)
        .filter(ItemVenda.venda_id == UUID(venda_id))
        .count()
        == 1
    )


def test_api_itens_venda_consulta_e_mutacao_bloqueada(
    client_auth: TestClient,
    venda_service: VendaService,
    cenario: dict[str, Any],
    db_session: Session,
) -> None:
    """Pacote 4.3 — /itens-venda: GET ok; POST/PUT/DELETE → 405."""
    venda = venda_service.criar(
        _venda_create(
            cenario,
            numero="V-ITENS",
            itens=[
                {
                    "produto_id": cenario["produto_a"].id,
                    "quantidade": Decimal("1"),
                    "valor_unitario": Decimal("9.00"),
                }
            ],
        )
    )
    item = (
        db_session.query(ItemVenda)
        .filter(ItemVenda.venda_id == venda.id)
        .one()
    )

    lista = client_auth.get("/itens-venda")
    assert lista.status_code == 200
    assert len(lista.json()) >= 1
    assert client_auth.get(f"/itens-venda/{item.id}").status_code == 200

    criar = client_auth.post(
        "/itens-venda",
        json={
            "venda_id": str(venda.id),
            "produto_id": cenario["produto_b"].id,
            "quantidade": "2",
            "valor_unitario": "3.00",
            "valor_total": "6.00",
        },
    )
    assert criar.status_code == 405

    assert (
        client_auth.put(
            f"/itens-venda/{item.id}",
            json={"quantidade": "99"},
        ).status_code
        == 405
    )
    assert client_auth.delete(f"/itens-venda/{item.id}").status_code == 405

    db_session.refresh(item)
    assert item.ativo is True
    assert db_session.query(ItemVenda).filter(ItemVenda.ativo.is_(True)).count() == 1


def test_api_duplicada_e_inexistente(
    client_auth: TestClient,
    cenario: dict[str, Any],
) -> None:
    payload = {
        "cliente_id": cenario["cliente"].id,
        "data_venda": "2026-08-15",
        "numero": "V-409",
        "observacoes": "",
        "status": "ABERTA",
        "itens": [
            {
                "produto_id": cenario["produto_a"].id,
                "quantidade": "1",
                "valor_unitario": "10.00",
            }
        ],
    }
    assert client_auth.post("/vendas", json=payload).status_code == 201
    assert client_auth.post("/vendas", json=payload).status_code == 409
    assert client_auth.get(f"/vendas/{uuid4()}").status_code == 404
