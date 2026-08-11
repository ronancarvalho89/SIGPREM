"""
Testes do módulo Financeiro (EPIC 003 — ETAPA 2).
"""

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_current_usuario
from app.database.database import get_db
from app.main import app
from app.models.auditoria import Auditoria
from app.models.movimento_financeiro import MovimentoFinanceiro
from app.models.movimento_financeiro import TipoMovimentoFinanceiro
from app.models.usuario import Usuario
from app.repositories.movimento_financeiro_repository import (
    MovimentoFinanceiroRepository,
)
from app.schemas.movimento_financeiro import MovimentoFinanceiroCreate
from app.services.movimento_financeiro_service import (
    MovimentoFinanceiroNaoEncontrado,
)
from app.services.movimento_financeiro_service import MovimentoFinanceiroService


@pytest.fixture()
def financeiro_service(db_session: Session) -> MovimentoFinanceiroService:
    """MovimentoFinanceiroService na sessão de teste."""
    return MovimentoFinanceiroService(MovimentoFinanceiroRepository(db_session))


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
    """TestClient sem autenticação (somente override de DB)."""

    def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def _payload_criar(
    *,
    tipo: TipoMovimentoFinanceiro = TipoMovimentoFinanceiro.VENDA,
    data_movimento: date = date(2026, 8, 10),
    valor: Decimal = Decimal("100.00"),
    descricao: str = "movimento teste",
    observacao: str = "obs",
) -> MovimentoFinanceiroCreate:
    return MovimentoFinanceiroCreate(
        tipo=tipo,
        data_movimento=data_movimento,
        valor=valor,
        descricao=descricao,
        observacao=observacao,
    )


def _auditorias_financeiras(
    db_session: Session,
    *,
    entidade_id: int | None = None,
    acao: str | None = None,
) -> list[Auditoria]:
    query = db_session.query(Auditoria).filter(
        Auditoria.modulo == "financeiro",
        Auditoria.entidade == "MovimentoFinanceiro",
    )
    if entidade_id is not None:
        query = query.filter(Auditoria.entidade_id == entidade_id)
    if acao is not None:
        query = query.filter(Auditoria.acao == acao)
    return query.all()


# ---------------------------------------------------------------------------
# 3.1 criar
# ---------------------------------------------------------------------------


def test_criar_movimento_persiste_campos(
    financeiro_service: MovimentoFinanceiroService,
) -> None:
    movimento = financeiro_service.criar(
        _payload_criar(
            tipo=TipoMovimentoFinanceiro.VENDA,
            valor=Decimal("250.50"),
            descricao="venda avulsa",
            observacao="caixa",
        )
    )

    assert movimento.id is not None
    assert movimento.tipo == TipoMovimentoFinanceiro.VENDA
    assert movimento.data_movimento == date(2026, 8, 10)
    assert Decimal(str(movimento.valor)) == Decimal("250.50")
    assert movimento.descricao == "venda avulsa"
    assert movimento.observacao == "caixa"
    assert movimento.ativo is True

    encontrado = financeiro_service.buscar_por_id(movimento.id)
    assert encontrado.id == movimento.id


def test_criar_movimento_registra_auditoria(
    financeiro_service: MovimentoFinanceiroService,
    db_session: Session,
) -> None:
    movimento = financeiro_service.criar(_payload_criar())

    auditorias = _auditorias_financeiras(
        db_session,
        entidade_id=movimento.id,
        acao="criar",
    )
    assert len(auditorias) == 1
    assert auditorias[0].modulo == "financeiro"
    assert auditorias[0].entidade == "MovimentoFinanceiro"
    assert auditorias[0].entidade_id == movimento.id
    assert auditorias[0].usuario_id is None  # chamada direta sem usuário


# ---------------------------------------------------------------------------
# 3.2 registrar vs criar
# ---------------------------------------------------------------------------


def test_registrar_nao_commita_nem_audita(
    financeiro_service: MovimentoFinanceiroService,
    db_session: Session,
) -> None:
    movimento = financeiro_service.registrar(
        tipo=TipoMovimentoFinanceiro.COMPRA_CONCRETO,
        data=date(2026, 8, 11),
        valor=Decimal("80.00"),
        descricao="compra em TX",
        observacao="sem commit",
    )

    assert movimento.id is None
    assert movimento in db_session
    assert _auditorias_financeiras(db_session) == []

    db_session.rollback()

    assert (
        db_session.query(MovimentoFinanceiro)
        .filter(MovimentoFinanceiro.descricao == "compra em TX")
        .count()
        == 0
    )


def test_criar_commita_e_audita_diferente_de_registrar(
    financeiro_service: MovimentoFinanceiroService,
    db_session: Session,
) -> None:
    criado = financeiro_service.criar(
        _payload_criar(descricao="via criar", valor=Decimal("10.00"))
    )
    assert criado.id is not None
    assert len(_auditorias_financeiras(db_session, acao="criar")) == 1

    registrado = financeiro_service.registrar(
        tipo=TipoMovimentoFinanceiro.PRODUCAO,
        data=date(2026, 8, 12),
        valor=Decimal("20.00"),
        descricao="via registrar",
    )
    assert registrado.id is None
    assert (
        len(
            _auditorias_financeiras(
                db_session,
                acao="criar",
            )
        )
        == 1
    )

    db_session.commit()
    db_session.refresh(registrado)
    assert registrado.id is not None
    assert (
        len(
            _auditorias_financeiras(
                db_session,
                entidade_id=registrado.id,
            )
        )
        == 0
    )


def test_registrar_reutilizavel_em_transacao_com_commit(
    financeiro_service: MovimentoFinanceiroService,
    db_session: Session,
) -> None:
    movimento = financeiro_service.registrar(
        tipo=TipoMovimentoFinanceiro.VENDA,
        data=date(2026, 8, 13),
        valor=Decimal("55.00"),
        descricao="tx ok",
    )
    db_session.commit()
    db_session.refresh(movimento)

    assert movimento.id is not None
    assert financeiro_service.buscar_por_id(movimento.id).descricao == "tx ok"


# ---------------------------------------------------------------------------
# 4. Entradas e saídas
# ---------------------------------------------------------------------------


def test_entrada_e_saida_no_fluxo_caixa(
    financeiro_service: MovimentoFinanceiroService,
) -> None:
    financeiro_service.criar(
        _payload_criar(
            tipo=TipoMovimentoFinanceiro.VENDA,
            valor=Decimal("100.00"),
            descricao="entrada",
        )
    )
    financeiro_service.criar(
        _payload_criar(
            tipo=TipoMovimentoFinanceiro.COMPRA_CONCRETO,
            valor=Decimal("40.00"),
            descricao="saida compra",
        )
    )
    financeiro_service.criar(
        _payload_criar(
            tipo=TipoMovimentoFinanceiro.PRODUCAO,
            valor=Decimal("10.00"),
            descricao="saida producao",
        )
    )

    fluxo = financeiro_service.fluxo_caixa()

    assert fluxo["total_entradas"] == Decimal("100.00")
    assert fluxo["total_saidas"] == Decimal("50.00")
    assert fluxo["saldo"] == Decimal("50.00")
    assert fluxo["quantidade_lancamentos"] == 3
    assert fluxo["total_por_tipo"]["VENDA"] == Decimal("100.00")
    assert fluxo["total_por_tipo"]["COMPRA_CONCRETO"] == Decimal("40.00")
    assert fluxo["total_por_tipo"]["PRODUCAO"] == Decimal("10.00")


def test_ajuste_nao_conta_como_entrada_nem_saida(
    financeiro_service: MovimentoFinanceiroService,
) -> None:
    financeiro_service.criar(
        _payload_criar(
            tipo=TipoMovimentoFinanceiro.AJUSTE,
            valor=Decimal("99.00"),
            descricao="ajuste",
        )
    )

    fluxo = financeiro_service.fluxo_caixa()

    assert fluxo["total_entradas"] == Decimal("0")
    assert fluxo["total_saidas"] == Decimal("0")
    assert fluxo["saldo"] == Decimal("0")
    assert fluxo["quantidade_lancamentos"] == 1
    assert fluxo["total_por_tipo"]["AJUSTE"] == Decimal("99.00")


# ---------------------------------------------------------------------------
# 5. Fluxo de caixa
# ---------------------------------------------------------------------------


def test_fluxo_caixa_sem_movimentos(
    financeiro_service: MovimentoFinanceiroService,
) -> None:
    fluxo = financeiro_service.fluxo_caixa()

    assert fluxo["total_entradas"] == Decimal("0")
    assert fluxo["total_saidas"] == Decimal("0")
    assert fluxo["saldo"] == Decimal("0")
    assert fluxo["quantidade_lancamentos"] == 0
    assert set(fluxo["total_por_tipo"].keys()) == {
        tipo.value for tipo in TipoMovimentoFinanceiro
    }


def test_fluxo_caixa_periodo_inclusivo_e_limites(
    financeiro_service: MovimentoFinanceiroService,
) -> None:
    financeiro_service.criar(
        _payload_criar(
            data_movimento=date(2026, 8, 1),
            valor=Decimal("10.00"),
            descricao="antes",
        )
    )
    financeiro_service.criar(
        _payload_criar(
            data_movimento=date(2026, 8, 5),
            valor=Decimal("20.00"),
            descricao="inicio",
        )
    )
    financeiro_service.criar(
        _payload_criar(
            data_movimento=date(2026, 8, 10),
            valor=Decimal("30.00"),
            descricao="fim",
        )
    )
    financeiro_service.criar(
        _payload_criar(
            data_movimento=date(2026, 8, 15),
            valor=Decimal("40.00"),
            descricao="depois",
        )
    )

    fluxo = financeiro_service.fluxo_caixa_periodo(
        date(2026, 8, 5),
        date(2026, 8, 10),
    )

    assert fluxo["quantidade_lancamentos"] == 2
    assert fluxo["total_entradas"] == Decimal("50.00")
    assert fluxo["saldo"] == Decimal("50.00")


# ---------------------------------------------------------------------------
# 6. Soft delete
# ---------------------------------------------------------------------------


def test_soft_delete_remove_do_fluxo_e_preserva_registro(
    financeiro_service: MovimentoFinanceiroService,
    db_session: Session,
) -> None:
    movimento = financeiro_service.criar(
        _payload_criar(valor=Decimal("70.00"), descricao="a inativar")
    )
    assert financeiro_service.fluxo_caixa()["quantidade_lancamentos"] == 1

    inativado = financeiro_service.excluir(movimento.id)

    assert inativado.ativo is False
    assert financeiro_service.fluxo_caixa()["quantidade_lancamentos"] == 0
    assert (
        db_session.query(MovimentoFinanceiro)
        .filter(MovimentoFinanceiro.id == movimento.id)
        .one()
        .ativo
        is False
    )
    with pytest.raises(MovimentoFinanceiroNaoEncontrado):
        financeiro_service.buscar_por_id(movimento.id)

    auditorias = _auditorias_financeiras(
        db_session,
        entidade_id=movimento.id,
        acao="inativar",
    )
    assert len(auditorias) == 1


# ---------------------------------------------------------------------------
# 8. Rollback com registrar
# ---------------------------------------------------------------------------


def test_registrar_em_transacao_com_rollback_nao_persiste(
    financeiro_service: MovimentoFinanceiroService,
    db_session: Session,
) -> None:
    try:
        financeiro_service.registrar(
            tipo=TipoMovimentoFinanceiro.VENDA,
            data=date(2026, 8, 20),
            valor=Decimal("15.00"),
            descricao="deve sumir",
        )
        raise RuntimeError("falha simulada na transacao")
    except RuntimeError:
        db_session.rollback()

    assert financeiro_service.fluxo_caixa()["quantidade_lancamentos"] == 0
    assert (
        db_session.query(MovimentoFinanceiro)
        .filter(MovimentoFinanceiro.descricao == "deve sumir")
        .count()
        == 0
    )


# ---------------------------------------------------------------------------
# 10. API
# ---------------------------------------------------------------------------


def test_api_movimentos_exige_autenticacao(client_anon: TestClient) -> None:
    response = client_anon.get("/movimentos-financeiros")
    assert response.status_code == 401


def test_api_fluxo_caixa_exige_autenticacao(client_anon: TestClient) -> None:
    response = client_anon.get("/financeiro/fluxo-caixa")
    assert response.status_code == 401


def test_api_auditoria_recebe_usuario_id(
    client_auth: TestClient,
    db_session: Session,
    usuario: Usuario,
) -> None:
    criar = client_auth.post(
        "/movimentos-financeiros",
        json={
            "tipo": "VENDA",
            "data_movimento": "2026-08-10",
            "valor": "80.00",
            "descricao": "api aud",
            "observacao": "",
        },
    )
    assert criar.status_code == 201
    movimento_id = criar.json()["id"]

    auditoria = (
        db_session.query(Auditoria)
        .filter(
            Auditoria.modulo == "financeiro",
            Auditoria.acao == "criar",
            Auditoria.entidade_id == movimento_id,
        )
        .one()
    )
    assert auditoria.usuario_id == usuario.id


def test_api_criar_listar_e_fluxo_caixa(client_auth: TestClient) -> None:
    criar = client_auth.post(
        "/movimentos-financeiros",
        json={
            "tipo": "VENDA",
            "data_movimento": "2026-08-10",
            "valor": "120.00",
            "descricao": "api venda",
            "observacao": "",
        },
    )
    assert criar.status_code == 201
    body = criar.json()
    assert body["tipo"] == "VENDA"
    assert Decimal(str(body["valor"])) == Decimal("120.00")

    client_auth.post(
        "/movimentos-financeiros",
        json={
            "tipo": "COMPRA_CONCRETO",
            "data_movimento": "2026-08-10",
            "valor": "20.00",
            "descricao": "api compra",
            "observacao": "",
        },
    )

    lista = client_auth.get("/movimentos-financeiros")
    assert lista.status_code == 200
    assert len(lista.json()) == 2

    fluxo = client_auth.get("/financeiro/fluxo-caixa")
    assert fluxo.status_code == 200
    dados = fluxo.json()
    assert Decimal(str(dados["total_entradas"])) == Decimal("120.00")
    assert Decimal(str(dados["total_saidas"])) == Decimal("20.00")
    assert Decimal(str(dados["saldo"])) == Decimal("100.00")


def test_api_fluxo_caixa_periodo_e_validacao(client_auth: TestClient) -> None:
    client_auth.post(
        "/movimentos-financeiros",
        json={
            "tipo": "VENDA",
            "data_movimento": "2026-08-08",
            "valor": "50.00",
            "descricao": "periodo",
            "observacao": "",
        },
    )

    ok = client_auth.get(
        "/financeiro/fluxo-caixa/periodo",
        params={
            "data_inicial": "2026-08-08",
            "data_final": "2026-08-08",
        },
    )
    assert ok.status_code == 200
    assert ok.json()["quantidade_lancamentos"] == 1

    invalido = client_auth.get(
        "/financeiro/fluxo-caixa/periodo",
        params={
            "data_inicial": "2026-08-10",
            "data_final": "2026-08-01",
        },
    )
    assert invalido.status_code == 422


def test_api_buscar_inexistente(client_auth: TestClient) -> None:
    response = client_auth.get("/movimentos-financeiros/99999")
    assert response.status_code == 404
