"""
Testes do contrato /itens-venda (EPIC 004 — Pacote 4.3).

Opção A: mutações independentes bloqueadas; consulta liberada.
Criação completa permanece em POST /vendas.
"""

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_current_usuario
from app.database.database import get_db
from app.main import app
from app.models.cliente import Cliente
from app.models.item_venda import ItemVenda
from app.models.movimento_estoque import TipoMovimentoEstoque
from app.models.produto import CategoriaProduto
from app.models.produto import Produto
from app.models.produto import TipoProduto
from app.models.produto import UnidadeProduto
from app.models.usuario import Usuario
from app.models.venda import Venda
from app.repositories.item_venda_repository import ItemVendaRepository
from app.repositories.movimento_estoque_repository import (
    MovimentoEstoqueRepository,
)
from app.repositories.venda_repository import VendaRepository
from app.schemas.item_venda import ItemVendaCreate
from app.schemas.item_venda import ItemVendaUpdate
from app.schemas.movimento_estoque import MovimentoEstoqueCreate
from app.schemas.venda import VendaCreate
from app.services.item_venda_service import ItemVendaService
from app.services.item_venda_service import OperacaoItemVendaNaoPermitida
from app.services.movimento_estoque_service import MovimentoEstoqueService
from app.services.venda_service import VendaService


@pytest.fixture()
def estoque_service(db_session: Session) -> MovimentoEstoqueService:
    return MovimentoEstoqueService(MovimentoEstoqueRepository(db_session))


@pytest.fixture()
def venda_service(db_session: Session) -> VendaService:
    return VendaService(VendaRepository(db_session))


@pytest.fixture()
def item_service(db_session: Session) -> ItemVendaService:
    return ItemVendaService(ItemVendaRepository(db_session))


@pytest.fixture()
def cenario(
    db_session: Session,
    estoque_service: MovimentoEstoqueService,
) -> dict[str, Any]:
    cliente = Cliente(
        razao_social="Cliente Itens Venda",
        nome_fantasia="Itens",
        cpf_cnpj="22333444000192",
        telefone="",
        whatsapp="",
        email="",
        observacao="",
    )
    produto = Produto(
        codigo="ITV-A",
        descricao="Produto Item Venda",
        categoria=CategoriaProduto.BLOQUETE,
        modelo="A",
        unidade=UnidadeProduto.UN,
        concreto_por_unidade=Decimal("0"),
        tipo_produto=TipoProduto.PRE_MOLDADO,
    )
    db_session.add_all([cliente, produto])
    db_session.commit()
    db_session.refresh(cliente)
    db_session.refresh(produto)

    estoque_service.criar(
        MovimentoEstoqueCreate(
            data=date(2026, 8, 1),
            produto_id=produto.id,
            quantidade=Decimal("100"),
            tipo=TipoMovimentoEstoque.ENTRADA,
            observacao="saldo inicial itens-venda",
        )
    )
    return {"cliente": cliente, "produto": produto}


@pytest.fixture()
def venda_com_item(
    venda_service: VendaService,
    cenario: dict[str, Any],
) -> Venda:
    return venda_service.criar(
        VendaCreate(
            cliente_id=cenario["cliente"].id,
            data_venda=date(2026, 8, 15),
            numero="V-ITV-1",
            valor_total=Decimal("0"),
            observacoes="",
            status="ABERTA",
            itens=[
                {
                    "produto_id": cenario["produto"].id,
                    "quantidade": Decimal("10"),
                    "valor_unitario": Decimal("5.00"),
                }
            ],
        )
    )


@pytest.fixture()
def client_auth(db_session: Session, usuario: Usuario):
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
    def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def _payload_item(venda_id: UUID, produto_id: int) -> dict[str, Any]:
    return {
        "venda_id": str(venda_id),
        "produto_id": produto_id,
        "quantidade": "2",
        "valor_unitario": "3.00",
        "valor_total": "6.00",
    }


# ---------------------------------------------------------------------------
# Service — mutações bloqueadas
# ---------------------------------------------------------------------------


def test_service_criar_bloqueado_sem_efeito(
    item_service: ItemVendaService,
    venda_com_item: Venda,
    cenario: dict[str, Any],
    db_session: Session,
    estoque_service: MovimentoEstoqueService,
) -> None:
    total_antes = Decimal(str(venda_com_item.valor_total))
    itens_antes = db_session.query(ItemVenda).count()
    saldo_antes = estoque_service.saldo_produto(cenario["produto"].id)

    with pytest.raises(OperacaoItemVendaNaoPermitida):
        item_service.criar(
            ItemVendaCreate(
                venda_id=venda_com_item.id,
                produto_id=cenario["produto"].id,
                quantidade=Decimal("2"),
                valor_unitario=Decimal("3.00"),
                valor_total=Decimal("6.00"),
            )
        )

    db_session.refresh(venda_com_item)
    assert db_session.query(ItemVenda).count() == itens_antes
    assert Decimal(str(venda_com_item.valor_total)) == total_antes
    assert estoque_service.saldo_produto(cenario["produto"].id) == saldo_antes


def test_service_atualizar_e_excluir_bloqueados(
    item_service: ItemVendaService,
    venda_com_item: Venda,
    db_session: Session,
) -> None:
    item = (
        db_session.query(ItemVenda)
        .filter(ItemVenda.venda_id == venda_com_item.id)
        .one()
    )

    with pytest.raises(OperacaoItemVendaNaoPermitida):
        item_service.atualizar(
            item.id,
            ItemVendaUpdate(quantidade=Decimal("99")),
        )

    with pytest.raises(OperacaoItemVendaNaoPermitida):
        item_service.excluir(item.id)

    db_session.refresh(item)
    assert item.ativo is True
    assert Decimal(str(item.quantidade)) == Decimal("10")


# ---------------------------------------------------------------------------
# API — consulta + mutações bloqueadas
# ---------------------------------------------------------------------------


def test_api_itens_venda_exige_autenticacao(client_anon: TestClient) -> None:
    assert client_anon.get("/itens-venda").status_code == 401
    assert client_anon.post("/itens-venda", json={}).status_code == 401


def test_api_listar_e_buscar_item_criado_via_venda(
    client_auth: TestClient,
    venda_com_item: Venda,
    db_session: Session,
) -> None:
    item = (
        db_session.query(ItemVenda)
        .filter(ItemVenda.venda_id == venda_com_item.id)
        .one()
    )

    lista = client_auth.get("/itens-venda")
    assert lista.status_code == 200
    ids = {row["id"] for row in lista.json()}
    assert item.id in ids

    detalhe = client_auth.get(f"/itens-venda/{item.id}")
    assert detalhe.status_code == 200
    assert detalhe.json()["venda_id"] == str(venda_com_item.id)
    assert Decimal(str(detalhe.json()["quantidade"])) == Decimal("10")


def test_api_buscar_inexistente_404(client_auth: TestClient) -> None:
    assert client_auth.get("/itens-venda/999999").status_code == 404


def test_api_criar_item_independente_retorna_405(
    client_auth: TestClient,
    venda_com_item: Venda,
    cenario: dict[str, Any],
    db_session: Session,
    estoque_service: MovimentoEstoqueService,
) -> None:
    itens_antes = db_session.query(ItemVenda).count()
    total_antes = Decimal(str(venda_com_item.valor_total))
    saldo_antes = estoque_service.saldo_produto(cenario["produto"].id)

    response = client_auth.post(
        "/itens-venda",
        json=_payload_item(venda_com_item.id, cenario["produto"].id),
    )
    assert response.status_code == 405
    assert "POST /vendas" in response.json()["detail"]

    db_session.refresh(venda_com_item)
    assert db_session.query(ItemVenda).count() == itens_antes
    assert Decimal(str(venda_com_item.valor_total)) == total_antes
    assert estoque_service.saldo_produto(cenario["produto"].id) == saldo_antes


def test_api_update_delete_bloqueados_sem_efeito(
    client_auth: TestClient,
    venda_com_item: Venda,
    db_session: Session,
    estoque_service: MovimentoEstoqueService,
    cenario: dict[str, Any],
) -> None:
    item = (
        db_session.query(ItemVenda)
        .filter(ItemVenda.venda_id == venda_com_item.id)
        .one()
    )
    saldo_antes = estoque_service.saldo_produto(cenario["produto"].id)
    total_antes = Decimal(str(venda_com_item.valor_total))

    atualizar = client_auth.put(
        f"/itens-venda/{item.id}",
        json={"quantidade": "99", "valor_total": "495.00"},
    )
    assert atualizar.status_code == 405

    excluir = client_auth.delete(f"/itens-venda/{item.id}")
    assert excluir.status_code == 405

    db_session.refresh(item)
    db_session.refresh(venda_com_item)
    assert item.ativo is True
    assert Decimal(str(item.quantidade)) == Decimal("10")
    assert Decimal(str(venda_com_item.valor_total)) == total_antes
    assert estoque_service.saldo_produto(cenario["produto"].id) == saldo_antes


def test_api_mutacao_bloqueada_preserva_consistencia_venda(
    client_auth: TestClient,
    venda_com_item: Venda,
    cenario: dict[str, Any],
    db_session: Session,
    estoque_service: MovimentoEstoqueService,
) -> None:
    """
    Rollback/sem efeito parcial: tentativa de mutação não altera
    ItemVenda, total da Venda nem estoque.
    """
    assert Decimal(str(venda_com_item.valor_total)) == Decimal("50.00")
    assert estoque_service.saldo_produto(cenario["produto"].id) == Decimal(
        "90"
    )

    for _ in range(2):
        assert (
            client_auth.post(
                "/itens-venda",
                json=_payload_item(
                    venda_com_item.id,
                    cenario["produto"].id,
                ),
            ).status_code
            == 405
        )

    assert db_session.query(ItemVenda).count() == 1
    db_session.refresh(venda_com_item)
    assert Decimal(str(venda_com_item.valor_total)) == Decimal("50.00")
    assert estoque_service.saldo_produto(cenario["produto"].id) == Decimal(
        "90"
    )
