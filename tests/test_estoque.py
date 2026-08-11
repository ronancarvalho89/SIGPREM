"""
Testes do módulo Estoque (EPIC 003 — ETAPA 3).
"""

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_current_usuario
from app.database.database import get_db
from app.main import app
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
from app.schemas.item_inventario import ItemInventarioCreate
from app.schemas.movimento_estoque import MovimentoEstoqueCreate
from app.schemas.movimento_estoque import MovimentoEstoqueUpdate
from app.services.inventario_service import InventarioService
from app.services.movimento_estoque_service import MovimentoEstoqueNaoEncontrado
from app.services.movimento_estoque_service import MovimentoEstoqueService


@pytest.fixture()
def estoque_service(db_session: Session) -> MovimentoEstoqueService:
    """MovimentoEstoqueService na sessão de teste."""
    return MovimentoEstoqueService(MovimentoEstoqueRepository(db_session))


@pytest.fixture()
def produto_a(db_session: Session) -> Produto:
    """Produto A para testes de estoque."""
    item = Produto(
        codigo="EST-A",
        descricao="Produto Estoque A",
        categoria=CategoriaProduto.BLOQUETE,
        modelo="A1",
        unidade=UnidadeProduto.UN,
        concreto_por_unidade=Decimal("0"),
        tipo_produto=TipoProduto.PRE_MOLDADO,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


@pytest.fixture()
def produto_b(db_session: Session) -> Produto:
    """Produto B para isolamento de saldo."""
    item = Produto(
        codigo="EST-B",
        descricao="Produto Estoque B",
        categoria=CategoriaProduto.BLOQUETE,
        modelo="B1",
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


def _criar_movimento(
    service: MovimentoEstoqueService,
    produto_id: int,
    *,
    tipo: TipoMovimentoEstoque,
    quantidade: Decimal,
    data_mov: date = date(2026, 8, 10),
    observacao: str = "",
) -> MovimentoEstoque:
    return service.criar(
        MovimentoEstoqueCreate(
            data=data_mov,
            produto_id=produto_id,
            quantidade=quantidade,
            tipo=tipo,
            observacao=observacao,
        )
    )


# ---------------------------------------------------------------------------
# 2. CRUD
# ---------------------------------------------------------------------------


def test_criar_e_buscar_movimento(
    estoque_service: MovimentoEstoqueService,
    produto_a: Produto,
) -> None:
    movimento = _criar_movimento(
        estoque_service,
        produto_a.id,
        tipo=TipoMovimentoEstoque.ENTRADA,
        quantidade=Decimal("25.00"),
        observacao="entrada CRUD",
    )

    assert movimento.id is not None
    assert movimento.produto_id == produto_a.id
    assert movimento.tipo == TipoMovimentoEstoque.ENTRADA
    assert Decimal(str(movimento.quantidade)) == Decimal("25.00")
    assert movimento.ativo is True

    encontrado = estoque_service.buscar_por_id(movimento.id)
    assert encontrado.id == movimento.id
    assert encontrado.observacao == "entrada CRUD"


def test_listar_movimentos(
    estoque_service: MovimentoEstoqueService,
    produto_a: Produto,
) -> None:
    _criar_movimento(
        estoque_service,
        produto_a.id,
        tipo=TipoMovimentoEstoque.ENTRADA,
        quantidade=Decimal("10"),
    )
    _criar_movimento(
        estoque_service,
        produto_a.id,
        tipo=TipoMovimentoEstoque.SAIDA,
        quantidade=Decimal("3"),
    )

    lista = estoque_service.listar()
    assert len(lista) == 2


def test_atualizar_movimento(
    estoque_service: MovimentoEstoqueService,
    produto_a: Produto,
) -> None:
    movimento = _criar_movimento(
        estoque_service,
        produto_a.id,
        tipo=TipoMovimentoEstoque.ENTRADA,
        quantidade=Decimal("10"),
    )

    atualizado = estoque_service.atualizar(
        movimento.id,
        MovimentoEstoqueUpdate(
            quantidade=Decimal("15.00"),
            observacao="ajustado",
        ),
    )

    assert Decimal(str(atualizado.quantidade)) == Decimal("15.00")
    assert atualizado.observacao == "ajustado"


def test_buscar_inexistente(
    estoque_service: MovimentoEstoqueService,
) -> None:
    with pytest.raises(MovimentoEstoqueNaoEncontrado):
        estoque_service.buscar_por_id(99999)


# ---------------------------------------------------------------------------
# 3. Tipos
# ---------------------------------------------------------------------------


def test_persistir_entrada_e_saida(
    estoque_service: MovimentoEstoqueService,
    produto_a: Produto,
) -> None:
    entrada = _criar_movimento(
        estoque_service,
        produto_a.id,
        tipo=TipoMovimentoEstoque.ENTRADA,
        quantidade=Decimal("100"),
    )
    saida = _criar_movimento(
        estoque_service,
        produto_a.id,
        tipo=TipoMovimentoEstoque.SAIDA,
        quantidade=Decimal("30"),
    )

    assert entrada.tipo == TipoMovimentoEstoque.ENTRADA
    assert saida.tipo == TipoMovimentoEstoque.SAIDA


# ---------------------------------------------------------------------------
# 4. Saldo
# ---------------------------------------------------------------------------


def test_saldo_sem_movimentos(
    estoque_service: MovimentoEstoqueService,
    produto_a: Produto,
) -> None:
    assert estoque_service.saldo_produto(produto_a.id) == Decimal("0")


def test_saldo_somente_entrada(
    estoque_service: MovimentoEstoqueService,
    produto_a: Produto,
) -> None:
    _criar_movimento(
        estoque_service,
        produto_a.id,
        tipo=TipoMovimentoEstoque.ENTRADA,
        quantidade=Decimal("75"),
    )
    assert estoque_service.saldo_produto(produto_a.id) == Decimal("75")


def test_saldo_somente_saida_permite_negativo(
    estoque_service: MovimentoEstoqueService,
    produto_a: Produto,
) -> None:
    _criar_movimento(
        estoque_service,
        produto_a.id,
        tipo=TipoMovimentoEstoque.SAIDA,
        quantidade=Decimal("10"),
    )
    assert estoque_service.saldo_produto(produto_a.id) == Decimal("-10")


def test_saldo_entradas_e_saidas(
    estoque_service: MovimentoEstoqueService,
    produto_a: Produto,
) -> None:
    _criar_movimento(
        estoque_service,
        produto_a.id,
        tipo=TipoMovimentoEstoque.ENTRADA,
        quantidade=Decimal("100"),
    )
    _criar_movimento(
        estoque_service,
        produto_a.id,
        tipo=TipoMovimentoEstoque.ENTRADA,
        quantidade=Decimal("50"),
    )
    _criar_movimento(
        estoque_service,
        produto_a.id,
        tipo=TipoMovimentoEstoque.SAIDA,
        quantidade=Decimal("30"),
    )

    assert estoque_service.saldo_produto(produto_a.id) == Decimal("120")


# ---------------------------------------------------------------------------
# 5. Soft delete
# ---------------------------------------------------------------------------


def test_soft_delete_nao_participa_do_saldo(
    estoque_service: MovimentoEstoqueService,
    produto_a: Produto,
    db_session: Session,
) -> None:
    entrada = _criar_movimento(
        estoque_service,
        produto_a.id,
        tipo=TipoMovimentoEstoque.ENTRADA,
        quantidade=Decimal("50"),
    )
    assert estoque_service.saldo_produto(produto_a.id) == Decimal("50")

    inativado = estoque_service.excluir(entrada.id)

    assert inativado.ativo is False
    assert estoque_service.saldo_produto(produto_a.id) == Decimal("0")
    assert (
        db_session.query(MovimentoEstoque)
        .filter(MovimentoEstoque.id == entrada.id)
        .one()
        .ativo
        is False
    )
    with pytest.raises(MovimentoEstoqueNaoEncontrado):
        estoque_service.buscar_por_id(entrada.id)


# ---------------------------------------------------------------------------
# 8. Isolamento por produto
# ---------------------------------------------------------------------------


def test_saldo_isolado_por_produto(
    estoque_service: MovimentoEstoqueService,
    produto_a: Produto,
    produto_b: Produto,
) -> None:
    _criar_movimento(
        estoque_service,
        produto_a.id,
        tipo=TipoMovimentoEstoque.ENTRADA,
        quantidade=Decimal("100"),
    )
    _criar_movimento(
        estoque_service,
        produto_a.id,
        tipo=TipoMovimentoEstoque.SAIDA,
        quantidade=Decimal("20"),
    )
    _criar_movimento(
        estoque_service,
        produto_b.id,
        tipo=TipoMovimentoEstoque.ENTRADA,
        quantidade=Decimal("50"),
    )
    _criar_movimento(
        estoque_service,
        produto_b.id,
        tipo=TipoMovimentoEstoque.SAIDA,
        quantidade=Decimal("10"),
    )

    assert estoque_service.saldo_produto(produto_a.id) == Decimal("80")
    assert estoque_service.saldo_produto(produto_b.id) == Decimal("40")


# ---------------------------------------------------------------------------
# 9. Uso por InventarioService (caminho atual via Service)
# ---------------------------------------------------------------------------


def test_inventario_adicionar_item_usa_saldo_produto(
    estoque_service: MovimentoEstoqueService,
    produto_a: Produto,
    usuario: Usuario,
    db_session: Session,
) -> None:
    _criar_movimento(
        estoque_service,
        produto_a.id,
        tipo=TipoMovimentoEstoque.ENTRADA,
        quantidade=Decimal("42"),
    )

    inventario_service = InventarioService(InventarioRepository(db_session))
    inventario = inventario_service.criar(
        InventarioCreate(
            data_inventario=date(2026, 8, 15),
            usuario_id=usuario.id,
            observacao="usa saldo estoque",
        )
    )
    item = inventario_service.adicionar_item(
        inventario.id,
        ItemInventarioCreate(
            inventario_id=inventario.id,
            produto_id=produto_a.id,
            quantidade_sistema=Decimal("0"),
            quantidade_fisica=Decimal("0"),
            diferenca=Decimal("0"),
        ),
    )

    assert Decimal(str(item.quantidade_sistema)) == Decimal("42")
    assert estoque_service.saldo_produto(produto_a.id) == Decimal("42")


# ---------------------------------------------------------------------------
# EPIC 004 / 4.1 — registrar() vs criar()
# ---------------------------------------------------------------------------


def test_registrar_nao_commita(
    estoque_service: MovimentoEstoqueService,
    produto_a: Produto,
    db_session: Session,
) -> None:
    movimento = estoque_service.registrar(
        MovimentoEstoqueCreate(
            data=date(2026, 8, 10),
            produto_id=produto_a.id,
            quantidade=Decimal("12"),
            tipo=TipoMovimentoEstoque.ENTRADA,
            observacao="sem commit",
        )
    )

    assert movimento.id is None
    assert movimento in db_session
    assert estoque_service.saldo_produto(produto_a.id) == Decimal("0")

    db_session.rollback()

    assert (
        db_session.query(MovimentoEstoque)
        .filter(MovimentoEstoque.observacao == "sem commit")
        .count()
        == 0
    )


def test_registrar_flush_permite_saldo_na_mesma_sessao(
    estoque_service: MovimentoEstoqueService,
    produto_a: Produto,
) -> None:
    estoque_service.registrar(
        MovimentoEstoqueCreate(
            data=date(2026, 8, 10),
            produto_id=produto_a.id,
            quantidade=Decimal("8"),
            tipo=TipoMovimentoEstoque.ENTRADA,
            observacao="com flush",
        ),
        flush=True,
    )

    assert estoque_service.saldo_produto(produto_a.id) == Decimal("8")


def test_criar_continua_com_commit(
    estoque_service: MovimentoEstoqueService,
    produto_a: Produto,
    db_session: Session,
) -> None:
    movimento = estoque_service.criar(
        MovimentoEstoqueCreate(
            data=date(2026, 8, 10),
            produto_id=produto_a.id,
            quantidade=Decimal("5"),
            tipo=TipoMovimentoEstoque.ENTRADA,
            observacao="com commit",
        )
    )

    assert movimento.id is not None
    assert estoque_service.saldo_produto(produto_a.id) == Decimal("5")
    assert (
        db_session.query(MovimentoEstoque)
        .filter(MovimentoEstoque.id == movimento.id)
        .one()
        .ativo
        is True
    )


def test_venda_usa_registrar_sem_duplicar_e_rollback_remove_movimento(
    db_session: Session,
    produto_a: Produto,
) -> None:
    from app.models.cliente import Cliente
    from app.repositories.venda_repository import VendaRepository
    from app.schemas.venda import VendaCreate
    from app.services.venda_service import VendaService

    cliente = Cliente(
        razao_social="Cliente Estoque 4.1",
        cpf_cnpj="44445555000144",
    )
    db_session.add(cliente)
    db_session.commit()
    db_session.refresh(cliente)

    estoque_service = MovimentoEstoqueService(
        MovimentoEstoqueRepository(db_session)
    )
    estoque_service.criar(
        MovimentoEstoqueCreate(
            data=date(2026, 8, 1),
            produto_id=produto_a.id,
            quantidade=Decimal("20"),
            tipo=TipoMovimentoEstoque.ENTRADA,
            observacao="saldo base",
        )
    )

    venda_service = VendaService(VendaRepository(db_session))

    class FinanceiroQueFalha:
        def registrar(self, *args, **kwargs):
            raise RuntimeError("falha apos estoque")

    venda_service.financeiro_service = FinanceiroQueFalha()  # type: ignore[assignment]

    with pytest.raises(RuntimeError, match="falha apos estoque"):
        venda_service.criar(
            VendaCreate(
                cliente_id=cliente.id,
                data_venda=date(2026, 8, 15),
                numero="V-EST-41",
                valor_total=Decimal("0"),
                itens=[
                    {
                        "produto_id": produto_a.id,
                        "quantidade": Decimal("3"),
                        "valor_unitario": Decimal("10"),
                    }
                ],
            )
        )

    assert (
        db_session.query(MovimentoEstoque)
        .filter(MovimentoEstoque.observacao == "Venda V-EST-41")
        .count()
        == 0
    )
    assert estoque_service.saldo_produto(produto_a.id) == Decimal("20")


def test_producao_usa_registrar_sem_duplicar_e_rollback_remove_movimento(
    db_session: Session,
) -> None:
    from app.models.fornecedor import Fornecedor
    from app.models.funcionario import Funcionario
    from app.models.funcionario_valor_produto import FuncionarioValorProduto
    from app.repositories.compra_concreto_repository import (
        CompraConcretoRepository,
    )
    from app.repositories.producao_repository import ProducaoRepository
    from app.schemas.compra_concreto import CompraConcretoCreate
    from app.schemas.producao import ProducaoCreate
    from app.services.compra_concreto_service import CompraConcretoService
    from app.services.producao_service import ProducaoService

    fornecedor = Fornecedor(
        razao_social="Forn Estoque 4.1",
        cpf_cnpj="55556666000155",
    )
    funcionario = Funcionario(
        nome="Prod 4.1",
        cpf="77788899900",
        data_admissao=date(2026, 1, 1),
    )
    produto = Produto(
        codigo="EST-PRD",
        descricao="Produto Producao 4.1",
        categoria=CategoriaProduto.BLOQUETE,
        modelo="P",
        unidade=UnidadeProduto.UN,
        concreto_por_unidade=Decimal("1"),
        tipo_produto=TipoProduto.PRE_MOLDADO,
    )
    db_session.add_all([fornecedor, funcionario, produto])
    db_session.commit()
    for obj in (fornecedor, funcionario, produto):
        db_session.refresh(obj)

    compra = CompraConcretoService(CompraConcretoRepository(db_session)).criar(
        CompraConcretoCreate(
            fornecedor_id=fornecedor.id,
            data_compra=date(2026, 8, 1),
            nota_fiscal="NF-EST-41",
            quantidade_comprada=Decimal("10"),
            quantidade_recebida=Decimal("10"),
            valor_total=Decimal("100"),
        )
    )
    db_session.add(
        FuncionarioValorProduto(
            funcionario_id=funcionario.id,
            produto_id=produto.id,
            valor=Decimal("2"),
        )
    )
    db_session.commit()

    producao_service = ProducaoService(ProducaoRepository(db_session))

    class FinanceiroQueFalha:
        def registrar(self, *args, **kwargs):
            raise RuntimeError("falha apos estoque producao")

    producao_service.financeiro_service = FinanceiroQueFalha()  # type: ignore[assignment]

    with pytest.raises(RuntimeError, match="falha apos estoque producao"):
        producao_service.criar(
            ProducaoCreate(
                data=date(2026, 8, 12),
                funcionario_id=funcionario.id,
                produto_id=produto.id,
                compra_concreto_id=compra.id,
                quantidade_produzida=Decimal("2"),
            )
        )

    assert (
        db_session.query(MovimentoEstoque)
        .filter(
            MovimentoEstoque.observacao
            == "Entrada automática gerada pela produção."
        )
        .count()
        == 0
    )
    assert (
        MovimentoEstoqueService(MovimentoEstoqueRepository(db_session))
        .saldo_produto(produto.id)
        == Decimal("0")
    )


# ---------------------------------------------------------------------------
# 7. API
# ---------------------------------------------------------------------------


def test_api_estoque_exige_autenticacao(client_anon: TestClient) -> None:
    response = client_anon.get("/movimentos-estoque")
    assert response.status_code == 401


def test_api_criar_consultar_e_listar(
    client_auth: TestClient,
    produto_a: Produto,
) -> None:
    criar = client_auth.post(
        "/movimentos-estoque",
        json={
            "data": "2026-08-10",
            "produto_id": produto_a.id,
            "quantidade": "35.00",
            "tipo": "ENTRADA",
            "observacao": "api",
        },
    )
    assert criar.status_code == 201
    body = criar.json()
    assert body["tipo"] == "ENTRADA"
    assert Decimal(str(body["quantidade"])) == Decimal("35.00")
    movimento_id = body["id"]

    buscar = client_auth.get(f"/movimentos-estoque/{movimento_id}")
    assert buscar.status_code == 200
    assert buscar.json()["id"] == movimento_id

    lista = client_auth.get("/movimentos-estoque")
    assert lista.status_code == 200
    assert len(lista.json()) == 1


def test_api_buscar_inexistente(client_auth: TestClient) -> None:
    response = client_auth.get("/movimentos-estoque/99999")
    assert response.status_code == 404


def test_api_soft_delete(
    client_auth: TestClient,
    produto_a: Produto,
) -> None:
    criar = client_auth.post(
        "/movimentos-estoque",
        json={
            "data": "2026-08-10",
            "produto_id": produto_a.id,
            "quantidade": "10.00",
            "tipo": "ENTRADA",
            "observacao": "",
        },
    )
    movimento_id = criar.json()["id"]

    excluir = client_auth.delete(f"/movimentos-estoque/{movimento_id}")
    assert excluir.status_code == 200
    assert excluir.json()["ativo"] is False

    buscar = client_auth.get(f"/movimentos-estoque/{movimento_id}")
    assert buscar.status_code == 404
