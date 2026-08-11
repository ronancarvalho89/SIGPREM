"""
Testes do módulo Compras de Concreto (EPIC 003 — ETAPA 4).
"""

from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_current_usuario
from app.database.database import get_db
from app.main import app
from app.models.auditoria import Auditoria
from app.models.compra_concreto import CompraConcreto
from app.models.fornecedor import Fornecedor
from app.models.funcionario import Funcionario
from app.models.funcionario_valor_produto import FuncionarioValorProduto
from app.models.movimento_estoque import MovimentoEstoque
from app.models.movimento_financeiro import MovimentoFinanceiro
from app.models.movimento_financeiro import TipoMovimentoFinanceiro
from app.models.produto import CategoriaProduto
from app.models.produto import Produto
from app.models.produto import TipoProduto
from app.models.produto import UnidadeProduto
from app.models.producao import Producao
from app.models.usuario import Usuario
from app.repositories.compra_concreto_repository import CompraConcretoRepository
from app.repositories.movimento_estoque_repository import (
    MovimentoEstoqueRepository,
)
from app.repositories.producao_repository import ProducaoRepository
from app.schemas.compra_concreto import CompraConcretoCreate
from app.schemas.compra_concreto import CompraConcretoUpdate
from app.schemas.producao import ProducaoCreate
from app.services.compra_concreto_service import CompraConcretoDuplicada
from app.services.compra_concreto_service import CompraConcretoJaEfetivada
from app.services.compra_concreto_service import CompraConcretoNaoEncontrada
from app.services.compra_concreto_service import CompraConcretoService
from app.services.movimento_estoque_service import MovimentoEstoqueService
from app.services.producao_service import ProducaoService


@pytest.fixture()
def compra_service(db_session: Session) -> CompraConcretoService:
    """CompraConcretoService na sessão de teste."""
    return CompraConcretoService(CompraConcretoRepository(db_session))


@pytest.fixture()
def fornecedor(db_session: Session) -> Fornecedor:
    """Fornecedor ativo para compras de concreto."""
    item = Fornecedor(
        razao_social="Fornecedor Concreto Teste",
        cpf_cnpj="12345678000199",
        telefone="",
        email="",
        observacao="",
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


def _payload(
    fornecedor_id: int,
    *,
    nota_fiscal: str = "NF-001",
    quantidade_comprada: Decimal = Decimal("10.000"),
    quantidade_recebida: Decimal = Decimal("10.000"),
    valor_total: Decimal = Decimal("1000.00"),
    data_compra: date = date(2026, 8, 10),
) -> CompraConcretoCreate:
    return CompraConcretoCreate(
        fornecedor_id=fornecedor_id,
        data_compra=data_compra,
        nota_fiscal=nota_fiscal,
        quantidade_comprada=quantidade_comprada,
        quantidade_recebida=quantidade_recebida,
        valor_total=valor_total,
        observacao="compra teste",
    )


def _movimentos_compra(
    db_session: Session,
    compra_id: int,
) -> list[MovimentoFinanceiro]:
    return (
        db_session.query(MovimentoFinanceiro)
        .filter(
            MovimentoFinanceiro.tipo
            == TipoMovimentoFinanceiro.COMPRA_CONCRETO,
            MovimentoFinanceiro.observacao.contains(f"Compra ID {compra_id}"),
        )
        .all()
    )


# ---------------------------------------------------------------------------
# 2. CRUD
# ---------------------------------------------------------------------------


def test_criar_buscar_listar_compra(
    compra_service: CompraConcretoService,
    fornecedor: Fornecedor,
) -> None:
    compra = compra_service.criar(_payload(fornecedor.id))

    assert compra.id is not None
    assert compra.fornecedor_id == fornecedor.id
    assert compra.nota_fiscal == "NF-001"
    assert Decimal(str(compra.quantidade_recebida)) == Decimal("10.000")
    assert Decimal(str(compra.saldo)) == Decimal("10.000")
    assert compra.ativo is True

    encontrada = compra_service.buscar_por_id(compra.id)
    assert encontrada.id == compra.id
    assert len(compra_service.listar()) == 1


def test_nota_fiscal_duplicada(
    compra_service: CompraConcretoService,
    fornecedor: Fornecedor,
) -> None:
    compra_service.criar(_payload(fornecedor.id, nota_fiscal="NF-DUP"))

    with pytest.raises(CompraConcretoDuplicada):
        compra_service.criar(_payload(fornecedor.id, nota_fiscal="NF-DUP"))


def test_buscar_inexistente(
    compra_service: CompraConcretoService,
) -> None:
    with pytest.raises(CompraConcretoNaoEncontrada):
        compra_service.buscar_por_id(99999)


# ---------------------------------------------------------------------------
# 3. Saldo de concreto
# ---------------------------------------------------------------------------


def test_saldo_inicial_igual_quantidade_recebida(
    compra_service: CompraConcretoService,
    fornecedor: Fornecedor,
) -> None:
    compra = compra_service.criar(
        _payload(
            fornecedor.id,
            quantidade_comprada=Decimal("20.000"),
            quantidade_recebida=Decimal("18.500"),
            valor_total=Decimal("2000.00"),
            nota_fiscal="NF-SALDO",
        )
    )

    assert Decimal(str(compra.saldo)) == Decimal("18.500")
    assert Decimal(str(compra.saldo)) == Decimal(
        str(compra.quantidade_recebida)
    )


def test_saldo_reduz_apos_consumo_pela_producao(
    compra_service: CompraConcretoService,
    fornecedor: Fornecedor,
    db_session: Session,
) -> None:
    compra = compra_service.criar(
        _payload(
            fornecedor.id,
            quantidade_recebida=Decimal("10.000"),
            valor_total=Decimal("500.00"),
            nota_fiscal="NF-PROD",
        )
    )

    produto = Produto(
        codigo="COMP-P1",
        descricao="Produto consumo concreto",
        categoria=CategoriaProduto.BLOQUETE,
        modelo="M1",
        unidade=UnidadeProduto.UN,
        concreto_por_unidade=Decimal("0.500"),
        tipo_produto=TipoProduto.PRE_MOLDADO,
    )
    funcionario = Funcionario(
        nome="Operador",
        cpf="11122233344",
        telefone="",
        data_admissao=date(2026, 1, 1),
    )
    db_session.add_all([produto, funcionario])
    db_session.commit()
    db_session.refresh(produto)
    db_session.refresh(funcionario)

    valor = FuncionarioValorProduto(
        funcionario_id=funcionario.id,
        produto_id=produto.id,
        valor=Decimal("5.00"),
    )
    db_session.add(valor)
    db_session.commit()

    producao_service = ProducaoService(ProducaoRepository(db_session))
    producao_service.criar(
        ProducaoCreate(
            data=date(2026, 8, 11),
            funcionario_id=funcionario.id,
            produto_id=produto.id,
            compra_concreto_id=compra.id,
            quantidade_produzida=Decimal("4"),
            observacao="consome 2.000 de concreto",
        )
    )

    db_session.refresh(compra)
    # 10.000 - (4 * 0.500) = 8.000
    assert Decimal(str(compra.saldo)) == Decimal("8.000")


# ---------------------------------------------------------------------------
# 4. Financeiro
# ---------------------------------------------------------------------------


def test_criar_compra_gera_movimento_financeiro(
    compra_service: CompraConcretoService,
    fornecedor: Fornecedor,
    db_session: Session,
) -> None:
    compra = compra_service.criar(
        _payload(
            fornecedor.id,
            valor_total=Decimal("1500.75"),
            nota_fiscal="NF-FIN",
        )
    )

    movimentos = _movimentos_compra(db_session, compra.id)
    assert len(movimentos) == 1
    movimento = movimentos[0]
    assert movimento.tipo == TipoMovimentoFinanceiro.COMPRA_CONCRETO
    assert Decimal(str(movimento.valor)) == Decimal("1500.75")
    assert movimento.data_movimento == compra.data_compra
    assert movimento.descricao == "Compra de concreto"
    assert f"Compra ID {compra.id}" in movimento.observacao
    assert f"Fornecedor ID {fornecedor.id}" in movimento.observacao
    assert movimento.ativo is True


# ---------------------------------------------------------------------------
# 5–6. Transação / rollback
# ---------------------------------------------------------------------------


def test_rollback_quando_financeiro_falha(
    compra_service: CompraConcretoService,
    fornecedor: Fornecedor,
    db_session: Session,
) -> None:
    class FinanceiroQueFalha:
        def registrar(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("falha simulada no financeiro")

    compra_service.financeiro_service = FinanceiroQueFalha()  # type: ignore[assignment]

    with pytest.raises(RuntimeError, match="falha simulada"):
        compra_service.criar(
            _payload(fornecedor.id, nota_fiscal="NF-ROLL")
        )

    assert (
        db_session.query(CompraConcreto)
        .filter(CompraConcreto.nota_fiscal == "NF-ROLL")
        .count()
        == 0
    )
    assert (
        db_session.query(MovimentoFinanceiro)
        .filter(
            MovimentoFinanceiro.tipo
            == TipoMovimentoFinanceiro.COMPRA_CONCRETO
        )
        .count()
        == 0
    )


# ---------------------------------------------------------------------------
# 7–8. Update / exclusão — Política A (Pacote 4.6.3)
# ---------------------------------------------------------------------------


def _cenario_compra_com_producao(
    db_session: Session,
    compra_service: CompraConcretoService,
    fornecedor: Fornecedor,
    *,
    nota_fiscal: str,
) -> dict[str, Any]:
    """Compra com saldo parcialmente consumido por Produção."""
    compra = compra_service.criar(
        _payload(
            fornecedor.id,
            quantidade_recebida=Decimal("10.000"),
            valor_total=Decimal("500.00"),
            nota_fiscal=nota_fiscal,
        )
    )
    produto = Produto(
        codigo=f"C-{nota_fiscal}",
        descricao="Produto consumo concreto",
        categoria=CategoriaProduto.BLOQUETE,
        modelo="M1",
        unidade=UnidadeProduto.UN,
        concreto_por_unidade=Decimal("0.500"),
        tipo_produto=TipoProduto.PRE_MOLDADO,
    )
    funcionario = Funcionario(
        nome=f"Op {nota_fiscal}",
        cpf=f"{abs(hash(nota_fiscal)) % 10**11:011d}",
        telefone="",
        data_admissao=date(2026, 1, 1),
    )
    db_session.add_all([produto, funcionario])
    db_session.commit()
    db_session.refresh(produto)
    db_session.refresh(funcionario)
    db_session.add(
        FuncionarioValorProduto(
            funcionario_id=funcionario.id,
            produto_id=produto.id,
            valor=Decimal("5.00"),
        )
    )
    db_session.commit()

    producao = ProducaoService(ProducaoRepository(db_session)).criar(
        ProducaoCreate(
            data=date(2026, 8, 11),
            funcionario_id=funcionario.id,
            produto_id=produto.id,
            compra_concreto_id=compra.id,
            quantidade_produzida=Decimal("4"),
            observacao="consome 2.000",
        )
    )
    db_session.refresh(compra)
    return {
        "compra": compra,
        "produto": produto,
        "producao": producao,
    }


def test_atualizar_compra_efetivada_bloqueado(
    compra_service: CompraConcretoService,
    fornecedor: Fornecedor,
    db_session: Session,
) -> None:
    compra = compra_service.criar(
        _payload(
            fornecedor.id,
            quantidade_recebida=Decimal("10.000"),
            valor_total=Decimal("1000.00"),
            nota_fiscal="NF-UPD",
        )
    )
    movimentos_antes = _movimentos_compra(db_session, compra.id)
    valor_financeiro_antes = Decimal(str(movimentos_antes[0].valor))
    saldo_antes = Decimal(str(compra.saldo))
    qtd_antes = Decimal(str(compra.quantidade_recebida))
    mov_fin_antes = db_session.query(MovimentoFinanceiro).count()

    with pytest.raises(CompraConcretoJaEfetivada):
        compra_service.atualizar(
            compra.id,
            CompraConcretoUpdate(
                quantidade_recebida=Decimal("20.000"),
                valor_total=Decimal("2000.00"),
                observacao="alterada",
            ),
        )

    db_session.refresh(compra)
    assert compra.ativo is True
    assert Decimal(str(compra.saldo)) == saldo_antes
    assert Decimal(str(compra.quantidade_recebida)) == qtd_antes
    assert Decimal(str(compra.valor_total)) == Decimal("1000.00")
    assert compra.observacao == "compra teste"
    movimentos = _movimentos_compra(db_session, compra.id)
    assert len(movimentos) == 1
    assert Decimal(str(movimentos[0].valor)) == valor_financeiro_antes
    assert db_session.query(MovimentoFinanceiro).count() == mov_fin_antes


def test_excluir_compra_efetivada_bloqueado(
    compra_service: CompraConcretoService,
    fornecedor: Fornecedor,
    db_session: Session,
) -> None:
    compra = compra_service.criar(
        _payload(
            fornecedor.id,
            quantidade_recebida=Decimal("5.000"),
            valor_total=Decimal("300.00"),
            nota_fiscal="NF-DEL",
        )
    )
    mov_fin_antes = db_session.query(MovimentoFinanceiro).count()

    with pytest.raises(CompraConcretoJaEfetivada):
        compra_service.excluir(compra.id)

    db_session.refresh(compra)
    assert compra.ativo is True
    assert compra_service.buscar_por_id(compra.id).id == compra.id
    movimentos = _movimentos_compra(db_session, compra.id)
    assert len(movimentos) == 1
    assert movimentos[0].ativo is True
    assert db_session.query(MovimentoFinanceiro).count() == mov_fin_antes


def test_compra_parcialmente_consumida_protegida(
    compra_service: CompraConcretoService,
    fornecedor: Fornecedor,
    db_session: Session,
) -> None:
    """Compra com Produção parcial: update/delete bloqueados sem efeitos."""
    cenario = _cenario_compra_com_producao(
        db_session,
        compra_service,
        fornecedor,
        nota_fiscal="NF-CONS",
    )
    compra = cenario["compra"]
    producao = cenario["producao"]
    produto = cenario["produto"]
    estoque = MovimentoEstoqueService(MovimentoEstoqueRepository(db_session))

    assert Decimal(str(compra.saldo)) == Decimal("8.000")
    saldo_antes = Decimal(str(compra.saldo))
    saldo_estoque = estoque.saldo_produto(produto.id)
    fin_antes = len(_movimentos_compra(db_session, compra.id))
    prod_antes = db_session.query(Producao).count()
    mov_est_antes = db_session.query(MovimentoEstoque).count()

    with pytest.raises(CompraConcretoJaEfetivada):
        compra_service.atualizar(
            compra.id,
            CompraConcretoUpdate(valor_total=Decimal("999.00")),
        )
    with pytest.raises(CompraConcretoJaEfetivada):
        compra_service.excluir(compra.id)

    db_session.refresh(compra)
    db_session.refresh(producao)
    assert compra.ativo is True
    assert Decimal(str(compra.saldo)) == saldo_antes
    assert Decimal(str(compra.valor_total)) == Decimal("500.00")
    assert producao.ativo is True
    assert db_session.query(Producao).count() == prod_antes
    assert estoque.saldo_produto(produto.id) == saldo_estoque
    assert len(_movimentos_compra(db_session, compra.id)) == fin_antes
    assert db_session.query(MovimentoEstoque).count() == mov_est_antes


# ---------------------------------------------------------------------------
# 10. Auditoria
# ---------------------------------------------------------------------------


def test_compra_nao_registra_auditoria(
    compra_service: CompraConcretoService,
    fornecedor: Fornecedor,
    db_session: Session,
) -> None:
    compra_service.criar(_payload(fornecedor.id, nota_fiscal="NF-AUD"))

    assert (
        db_session.query(Auditoria)
        .filter(Auditoria.modulo == "compra")
        .count()
        == 0
    )
    assert (
        db_session.query(Auditoria)
        .filter(Auditoria.entidade == "CompraConcreto")
        .count()
        == 0
    )


# ---------------------------------------------------------------------------
# 9. API
# ---------------------------------------------------------------------------


def test_api_compras_exige_autenticacao(client_anon: TestClient) -> None:
    response = client_anon.get("/compras-concreto")
    assert response.status_code == 401


def test_api_criar_listar_update_delete_bloqueados(
    client_auth: TestClient,
    fornecedor: Fornecedor,
    db_session: Session,
) -> None:
    criar = client_auth.post(
        "/compras-concreto",
        json={
            "fornecedor_id": fornecedor.id,
            "data_compra": "2026-08-10",
            "nota_fiscal": "NF-API",
            "quantidade_comprada": "12.000",
            "quantidade_recebida": "12.000",
            "valor_total": "900.00",
            "observacao": "api",
        },
    )
    assert criar.status_code == 201
    body = criar.json()
    assert Decimal(str(body["saldo"])) == Decimal("12.000")
    compra_id = body["id"]

    lista = client_auth.get("/compras-concreto")
    assert lista.status_code == 200
    assert len(lista.json()) == 1

    buscar = client_auth.get(f"/compras-concreto/{compra_id}")
    assert buscar.status_code == 200

    fin_antes = len(_movimentos_compra(db_session, compra_id))

    atualizar = client_auth.put(
        f"/compras-concreto/{compra_id}",
        json={"observacao": "atualizada"},
    )
    assert atualizar.status_code == 400
    assert "efetivada" in atualizar.json()["detail"].lower()

    excluir = client_auth.delete(f"/compras-concreto/{compra_id}")
    assert excluir.status_code == 400
    assert "efetivada" in excluir.json()["detail"].lower()

    detalhe = client_auth.get(f"/compras-concreto/{compra_id}")
    assert detalhe.status_code == 200
    assert detalhe.json()["ativo"] is True
    assert detalhe.json()["observacao"] == "api"
    assert Decimal(str(detalhe.json()["saldo"])) == Decimal("12.000")
    assert len(_movimentos_compra(db_session, compra_id)) == fin_antes


def test_api_duplicada_e_inexistente(
    client_auth: TestClient,
    fornecedor: Fornecedor,
) -> None:
    payload = {
        "fornecedor_id": fornecedor.id,
        "data_compra": "2026-08-10",
        "nota_fiscal": "NF-409",
        "quantidade_comprada": "1.000",
        "quantidade_recebida": "1.000",
        "valor_total": "10.00",
        "observacao": "",
    }
    assert client_auth.post("/compras-concreto", json=payload).status_code == 201
    dup = client_auth.post("/compras-concreto", json=payload)
    assert dup.status_code == 409

    inexistente = client_auth.get("/compras-concreto/99999")
    assert inexistente.status_code == 404
