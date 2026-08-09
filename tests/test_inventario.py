"""
Testes do módulo Inventário (EPIC 002 — ETAPA 2).
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
from app.models.movimento_estoque import MovimentoEstoque
from app.models.movimento_estoque import TipoMovimentoEstoque
from app.models.produto import CategoriaProduto
from app.models.produto import Produto
from app.models.produto import TipoProduto
from app.models.produto import UnidadeProduto
from app.models.usuario import Usuario
from app.repositories.inventario_repository import InventarioRepository
from app.repositories.movimento_estoque_repository import (
    MovimentoEstoqueRepository,
)
from app.schemas.inventario import InventarioCreate
from app.schemas.inventario import InventarioUpdate
from app.schemas.item_inventario import ItemInventarioCreate
from app.schemas.movimento_estoque import MovimentoEstoqueCreate
from app.services.inventario_service import InventarioJaConcluido
from app.services.inventario_service import InventarioNaoEncontrado
from app.services.inventario_service import InventarioService
from app.services.inventario_service import InventarioStatusInvalido
from app.services.inventario_service import STATUS_INVENTARIO_ABERTO
from app.services.inventario_service import STATUS_INVENTARIO_CONCLUIDO
from app.services.movimento_estoque_service import MovimentoEstoqueService


@pytest.fixture()
def inventario_service(db_session: Session) -> InventarioService:
    """InventarioService na sessão de teste."""
    return InventarioService(InventarioRepository(db_session))


@pytest.fixture()
def estoque_service(db_session: Session) -> MovimentoEstoqueService:
    """MovimentoEstoqueService na sessão de teste."""
    return MovimentoEstoqueService(MovimentoEstoqueRepository(db_session))


@pytest.fixture()
def produto(db_session: Session) -> Produto:
    """Produto ativo para testes de inventário/estoque."""
    item = Produto(
        codigo="INV-001",
        descricao="Produto Inventário Teste",
        categoria=CategoriaProduto.BLOQUETE,
        modelo="M1",
        unidade=UnidadeProduto.UN,
        concreto_por_unidade=Decimal("0"),
        tipo_produto=TipoProduto.PRE_MOLDADO,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


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


def _criar_inventario(
    service: InventarioService,
    usuario: Usuario,
) -> object:
    return service.criar(
        InventarioCreate(
            data_inventario=date(2026, 8, 9),
            usuario_id=usuario.id,
            observacao="teste",
        )
    )


def _payload_item(
    inventario_id: int,
    produto_id: int,
) -> ItemInventarioCreate:
    return ItemInventarioCreate(
        inventario_id=inventario_id,
        produto_id=produto_id,
        quantidade_sistema=Decimal("0"),
        quantidade_fisica=Decimal("0"),
        diferenca=Decimal("0"),
    )


def _entrar_estoque(
    estoque_service: MovimentoEstoqueService,
    produto_id: int,
    quantidade: Decimal,
) -> None:
    estoque_service.criar(
        MovimentoEstoqueCreate(
            data=date(2026, 8, 1),
            produto_id=produto_id,
            quantidade=quantidade,
            tipo=TipoMovimentoEstoque.ENTRADA,
            observacao="saldo inicial teste",
        )
    )


# ---------------------------------------------------------------------------
# 2.1 CRUD
# ---------------------------------------------------------------------------


def test_criar_inventario(
    inventario_service: InventarioService,
    usuario: Usuario,
) -> None:
    inventario = _criar_inventario(inventario_service, usuario)

    assert inventario.id is not None
    assert inventario.usuario_id == usuario.id
    assert inventario.ativo is True
    assert inventario.status == STATUS_INVENTARIO_ABERTO


def test_consultar_inventario(
    inventario_service: InventarioService,
    usuario: Usuario,
) -> None:
    criado = _criar_inventario(inventario_service, usuario)
    encontrado = inventario_service.buscar_por_id(criado.id)

    assert encontrado.id == criado.id
    assert encontrado.observacao == "teste"


def test_atualizar_inventario(
    inventario_service: InventarioService,
    usuario: Usuario,
) -> None:
    criado = _criar_inventario(inventario_service, usuario)
    atualizado = inventario_service.atualizar(
        criado.id,
        InventarioUpdate(observacao="atualizado"),
    )

    assert atualizado.observacao == "atualizado"
    assert atualizado.status == STATUS_INVENTARIO_ABERTO


def test_listar_inventarios(
    inventario_service: InventarioService,
    usuario: Usuario,
) -> None:
    _criar_inventario(inventario_service, usuario)
    _criar_inventario(inventario_service, usuario)

    assert len(inventario_service.listar()) == 2


def test_soft_delete_inventario(
    inventario_service: InventarioService,
    usuario: Usuario,
    db_session: Session,
) -> None:
    criado = _criar_inventario(inventario_service, usuario)
    inventario_id = criado.id

    inativado = inventario_service.excluir(inventario_id)

    assert inativado.ativo is False
    with pytest.raises(InventarioNaoEncontrado):
        inventario_service.buscar_por_id(inventario_id)

    from app.models.inventario import Inventario

    fisico = (
        db_session.query(Inventario)
        .filter(Inventario.id == inventario_id)
        .first()
    )
    assert fisico is not None
    assert fisico.ativo is False


# ---------------------------------------------------------------------------
# 2.2 STATUS
# ---------------------------------------------------------------------------


def test_novo_inventario_inicia_aberto(
    inventario_service: InventarioService,
    usuario: Usuario,
) -> None:
    inventario = _criar_inventario(inventario_service, usuario)
    assert inventario.status == "aberto"


def test_api_resposta_expoe_status(
    client_auth: TestClient,
    usuario: Usuario,
) -> None:
    resposta = client_auth.post(
        "/inventarios",
        json={
            "data_inventario": "2026-08-09",
            "usuario_id": usuario.id,
            "observacao": "api status",
        },
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["status"] == "aberto"


def test_filtro_status_aberto(
    inventario_service: InventarioService,
    usuario: Usuario,
) -> None:
    aberto = _criar_inventario(inventario_service, usuario)
    concluido = _criar_inventario(inventario_service, usuario)
    inventario_service.concluir(concluido.id)

    resultado = inventario_service.listar_por_status("aberto")

    ids = {item.id for item in resultado}
    assert aberto.id in ids
    assert concluido.id not in ids


def test_filtro_status_concluido(
    inventario_service: InventarioService,
    usuario: Usuario,
) -> None:
    _criar_inventario(inventario_service, usuario)
    concluido = _criar_inventario(inventario_service, usuario)
    inventario_service.concluir(concluido.id)

    resultado = inventario_service.listar_por_status("concluido")

    assert len(resultado) == 1
    assert resultado[0].id == concluido.id
    assert resultado[0].status == STATUS_INVENTARIO_CONCLUIDO


def test_status_invalido(
    inventario_service: InventarioService,
) -> None:
    with pytest.raises(InventarioStatusInvalido):
        inventario_service.listar_por_status("invalidado")


def test_api_status_invalido(client_auth: TestClient) -> None:
    resposta = client_auth.get("/inventarios", params={"status": "xyz"})
    assert resposta.status_code == 400


# ---------------------------------------------------------------------------
# 2.3 ADICIONAR ITEM
# ---------------------------------------------------------------------------


def test_adicionar_item_carrega_saldo(
    inventario_service: InventarioService,
    estoque_service: MovimentoEstoqueService,
    usuario: Usuario,
    produto: Produto,
) -> None:
    _entrar_estoque(estoque_service, produto.id, Decimal("100"))
    inventario = _criar_inventario(inventario_service, usuario)

    item = inventario_service.adicionar_item(
        inventario.id,
        _payload_item(inventario.id, produto.id),
    )

    assert item.inventario_id == inventario.id
    assert item.produto_id == produto.id
    assert Decimal(str(item.quantidade_sistema)) == Decimal("100")


# ---------------------------------------------------------------------------
# 2.4 / 2.5 CONTAGEM E DIFERENÇA
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("fisica", "esperada"),
    [
        (Decimal("110"), Decimal("10")),
        (Decimal("90"), Decimal("-10")),
        (Decimal("100"), Decimal("0")),
    ],
)
def test_contagem_calcula_diferenca(
    inventario_service: InventarioService,
    estoque_service: MovimentoEstoqueService,
    usuario: Usuario,
    produto: Produto,
    fisica: Decimal,
    esperada: Decimal,
) -> None:
    _entrar_estoque(estoque_service, produto.id, Decimal("100"))
    inventario = _criar_inventario(inventario_service, usuario)
    item = inventario_service.adicionar_item(
        inventario.id,
        _payload_item(inventario.id, produto.id),
    )

    atualizado = inventario_service.item_inventario_service.registrar_quantidade_fisica(
        item.id,
        fisica,
    )

    assert Decimal(str(atualizado.quantidade_fisica)) == fisica
    assert Decimal(str(atualizado.diferenca)) == esperada


# ---------------------------------------------------------------------------
# 2.6 CONCLUSÃO
# ---------------------------------------------------------------------------


def test_concluir_gera_entrada_saida_e_ignora_zero(
    inventario_service: InventarioService,
    estoque_service: MovimentoEstoqueService,
    usuario: Usuario,
    db_session: Session,
) -> None:
    produtos = []
    for indice, codigo in enumerate(("P-ENT", "P-SAI", "P-ZERO"), start=1):
        prod = Produto(
            codigo=codigo,
            descricao=f"Produto {codigo}",
            categoria=CategoriaProduto.BLOQUETE,
            modelo="M",
            unidade=UnidadeProduto.UN,
            concreto_por_unidade=Decimal("0"),
            tipo_produto=TipoProduto.PRE_MOLDADO,
        )
        db_session.add(prod)
        db_session.commit()
        db_session.refresh(prod)
        produtos.append(prod)
        _entrar_estoque(estoque_service, prod.id, Decimal("100"))

    inventario = _criar_inventario(inventario_service, usuario)
    item_ent = inventario_service.adicionar_item(
        inventario.id,
        _payload_item(inventario.id, produtos[0].id),
    )
    item_sai = inventario_service.adicionar_item(
        inventario.id,
        _payload_item(inventario.id, produtos[1].id),
    )
    item_zero = inventario_service.adicionar_item(
        inventario.id,
        _payload_item(inventario.id, produtos[2].id),
    )

    inventario_service.item_inventario_service.registrar_quantidade_fisica(
        item_ent.id,
        Decimal("110"),
    )
    inventario_service.item_inventario_service.registrar_quantidade_fisica(
        item_sai.id,
        Decimal("90"),
    )
    inventario_service.item_inventario_service.registrar_quantidade_fisica(
        item_zero.id,
        Decimal("100"),
    )

    concluido = inventario_service.concluir(inventario.id)

    assert concluido.status == STATUS_INVENTARIO_CONCLUIDO

    movimentos = (
        db_session.query(MovimentoEstoque)
        .filter(MovimentoEstoque.ativo.is_(True))
        .filter(
            MovimentoEstoque.observacao
            == f"Ajuste inventário {inventario.id}"
        )
        .all()
    )
    assert len(movimentos) == 2

    por_produto = {m.produto_id: m for m in movimentos}
    assert por_produto[produtos[0].id].tipo == TipoMovimentoEstoque.ENTRADA
    assert Decimal(str(por_produto[produtos[0].id].quantidade)) == Decimal(
        "10"
    )
    assert por_produto[produtos[1].id].tipo == TipoMovimentoEstoque.SAIDA
    assert Decimal(str(por_produto[produtos[1].id].quantidade)) == Decimal(
        "10"
    )
    assert produtos[2].id not in por_produto

    auditorias = (
        db_session.query(Auditoria)
        .filter(
            Auditoria.modulo == "inventario",
            Auditoria.acao == "concluir",
            Auditoria.entidade_id == inventario.id,
        )
        .all()
    )
    assert len(auditorias) == 1


# ---------------------------------------------------------------------------
# 2.7 / 2.8 BLOQUEIO E CONCLUSÃO DUPLA
# ---------------------------------------------------------------------------


def test_bloqueio_apos_conclusao(
    inventario_service: InventarioService,
    estoque_service: MovimentoEstoqueService,
    usuario: Usuario,
    produto: Produto,
) -> None:
    _entrar_estoque(estoque_service, produto.id, Decimal("50"))
    inventario = _criar_inventario(inventario_service, usuario)
    item = inventario_service.adicionar_item(
        inventario.id,
        _payload_item(inventario.id, produto.id),
    )
    inventario_service.item_inventario_service.registrar_quantidade_fisica(
        item.id,
        Decimal("50"),
    )
    inventario_service.concluir(inventario.id)

    with pytest.raises(InventarioJaConcluido):
        inventario_service.adicionar_item(
            inventario.id,
            _payload_item(inventario.id, produto.id),
        )

    with pytest.raises(InventarioJaConcluido):
        inventario_service.item_inventario_service.registrar_quantidade_fisica(
            item.id,
            Decimal("60"),
        )

    with pytest.raises(InventarioJaConcluido):
        inventario_service.item_inventario_service.calcular_diferenca(item.id)

    with pytest.raises(InventarioJaConcluido):
        inventario_service.concluir(inventario.id)


def test_conclusao_dupla_nao_duplica_ajustes(
    inventario_service: InventarioService,
    estoque_service: MovimentoEstoqueService,
    usuario: Usuario,
    produto: Produto,
    db_session: Session,
) -> None:
    _entrar_estoque(estoque_service, produto.id, Decimal("100"))
    inventario = _criar_inventario(inventario_service, usuario)
    item = inventario_service.adicionar_item(
        inventario.id,
        _payload_item(inventario.id, produto.id),
    )
    inventario_service.item_inventario_service.registrar_quantidade_fisica(
        item.id,
        Decimal("110"),
    )

    inventario_service.concluir(inventario.id)
    with pytest.raises(InventarioJaConcluido):
        inventario_service.concluir(inventario.id)

    movimentos = (
        db_session.query(MovimentoEstoque)
        .filter(
            MovimentoEstoque.observacao
            == f"Ajuste inventário {inventario.id}"
        )
        .all()
    )
    assert len(movimentos) == 1

    auditorias = (
        db_session.query(Auditoria)
        .filter(
            Auditoria.acao == "concluir",
            Auditoria.entidade_id == inventario.id,
        )
        .all()
    )
    assert len(auditorias) == 1


# ---------------------------------------------------------------------------
# 2.9 API DE ITENS
# ---------------------------------------------------------------------------


def test_api_criar_item_usa_adicionar_item_com_saldo(
    client_auth: TestClient,
    inventario_service: InventarioService,
    estoque_service: MovimentoEstoqueService,
    usuario: Usuario,
    produto: Produto,
) -> None:
    _entrar_estoque(estoque_service, produto.id, Decimal("75"))
    inventario = _criar_inventario(inventario_service, usuario)

    resposta = client_auth.post(
        f"/inventario/{inventario.id}/itens",
        json={
            "inventario_id": inventario.id,
            "produto_id": produto.id,
            "quantidade_sistema": "0",
            "quantidade_fisica": "0",
            "diferenca": "0",
            "observacao": "",
        },
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["inventario_id"] == inventario.id
    assert Decimal(str(corpo["quantidade_sistema"])) == Decimal("75")


# ---------------------------------------------------------------------------
# 2.10 AUTENTICAÇÃO
# ---------------------------------------------------------------------------


def test_api_inventario_exige_autenticacao(
    client_anon: TestClient,
) -> None:
    resposta = client_anon.get("/inventarios")
    assert resposta.status_code == 401


def test_api_inventario_autenticado_permite_acesso(
    client_auth: TestClient,
) -> None:
    resposta = client_auth.get("/inventarios")
    assert resposta.status_code == 200
    assert isinstance(resposta.json(), list)


# ---------------------------------------------------------------------------
# 3. FLUXO COMPLETO
# ---------------------------------------------------------------------------


def test_fluxo_completo_inventario(
    inventario_service: InventarioService,
    estoque_service: MovimentoEstoqueService,
    usuario: Usuario,
    produto: Produto,
    db_session: Session,
) -> None:
    _entrar_estoque(estoque_service, produto.id, Decimal("100"))

    inventario = inventario_service.criar(
        InventarioCreate(
            data_inventario=date(2026, 8, 9),
            usuario_id=usuario.id,
            observacao="fluxo completo",
        )
    )
    assert inventario.status == STATUS_INVENTARIO_ABERTO

    item = inventario_service.adicionar_item(
        inventario.id,
        _payload_item(inventario.id, produto.id),
    )
    assert Decimal(str(item.quantidade_sistema)) == Decimal("100")

    item = inventario_service.item_inventario_service.registrar_quantidade_fisica(
        item.id,
        Decimal("110"),
    )
    assert Decimal(str(item.quantidade_fisica)) == Decimal("110")
    assert Decimal(str(item.diferenca)) == Decimal("10")

    concluido = inventario_service.concluir(inventario.id)
    assert concluido.status == STATUS_INVENTARIO_CONCLUIDO

    ajustes = (
        db_session.query(MovimentoEstoque)
        .filter(
            MovimentoEstoque.observacao
            == f"Ajuste inventário {inventario.id}"
        )
        .all()
    )
    assert len(ajustes) == 1
    assert ajustes[0].tipo == TipoMovimentoEstoque.ENTRADA
    assert Decimal(str(ajustes[0].quantidade)) == Decimal("10")

    auditorias = (
        db_session.query(Auditoria)
        .filter(
            Auditoria.modulo == "inventario",
            Auditoria.entidade_id == inventario.id,
            Auditoria.acao == "concluir",
        )
        .all()
    )
    assert len(auditorias) == 1

    with pytest.raises(InventarioJaConcluido):
        inventario_service.adicionar_item(
            inventario.id,
            _payload_item(inventario.id, produto.id),
        )
