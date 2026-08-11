"""
Testes do Dashboard (EPIC 003 — ETAPA 7).
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
from app.models.cliente import Cliente
from app.models.fornecedor import Fornecedor
from app.models.funcionario import Funcionario
from app.models.funcionario_valor_produto import FuncionarioValorProduto
from app.models.movimento_estoque import TipoMovimentoEstoque
from app.models.movimento_financeiro import TipoMovimentoFinanceiro
from app.models.produto import CategoriaProduto
from app.models.produto import Produto
from app.models.produto import TipoProduto
from app.models.produto import UnidadeProduto
from app.models.usuario import Usuario
from app.repositories.compra_concreto_repository import CompraConcretoRepository
from app.repositories.movimento_estoque_repository import (
    MovimentoEstoqueRepository,
)
from app.repositories.movimento_financeiro_repository import (
    MovimentoFinanceiroRepository,
)
from app.repositories.producao_repository import ProducaoRepository
from app.repositories.venda_repository import VendaRepository
from app.schemas.compra_concreto import CompraConcretoCreate
from app.schemas.movimento_estoque import MovimentoEstoqueCreate
from app.schemas.movimento_financeiro import MovimentoFinanceiroCreate
from app.schemas.producao import ProducaoCreate
from app.schemas.venda import VendaCreate
from app.services.compra_concreto_service import CompraConcretoService
from app.services.movimento_estoque_service import MovimentoEstoqueService
from app.services.movimento_financeiro_service import MovimentoFinanceiroService
from app.services.producao_service import ProducaoService
from app.services.venda_service import VendaService


BLOCOS = (
    "fluxo_financeiro",
    "comercial",
    "producao",
    "estoque",
    "executivo",
)


@pytest.fixture()
def client_auth(db_session: Session, usuario: Usuario):
    """TestClient autenticado."""

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


def _d(valor: Any) -> Decimal:
    return Decimal(str(valor))


def test_dashboard_exige_autenticacao(client_anon: TestClient) -> None:
    assert client_anon.get("/dashboard").status_code == 401


def test_dashboard_sem_dados(client_auth: TestClient) -> None:
    response = client_auth.get("/dashboard")
    assert response.status_code == 200
    dados = response.json()
    assert set(dados.keys()) == set(BLOCOS)

    assert _d(dados["fluxo_financeiro"]["total_entradas"]) == Decimal("0")
    assert _d(dados["fluxo_financeiro"]["total_saidas"]) == Decimal("0")
    assert _d(dados["fluxo_financeiro"]["saldo"]) == Decimal("0")
    assert dados["fluxo_financeiro"]["quantidade_lancamentos"] == 0

    assert dados["comercial"]["quantidade_vendas"] == 0
    assert _d(dados["comercial"]["valor_total_vendas"]) == Decimal("0")

    assert dados["producao"]["quantidade_producoes"] == 0
    assert _d(dados["producao"]["quantidade_total_produzida"]) == Decimal("0")

    assert dados["estoque"]["quantidade_movimentos"] == 0
    assert _d(dados["estoque"]["saldo_total_estoque"]) == Decimal("0")

    assert _d(dados["executivo"]["faturamento_total"]) == Decimal("0")
    assert dados["executivo"]["quantidade_clientes_atendidos"] == 0


def test_dashboard_com_dados_consolida_blocos(
    client_auth: TestClient,
    db_session: Session,
) -> None:
    cliente = Cliente(
        razao_social="Cliente Dashboard",
        cpf_cnpj="55667788000199",
    )
    fornecedor = Fornecedor(
        razao_social="Forn Dashboard",
        cpf_cnpj="66778899000111",
    )
    funcionario = Funcionario(
        nome="Func Dashboard",
        cpf="99887766554",
        data_admissao=date(2026, 1, 1),
    )
    produto = Produto(
        codigo="DASH-1",
        descricao="Produto Dashboard",
        categoria=CategoriaProduto.BLOQUETE,
        modelo="D",
        unidade=UnidadeProduto.UN,
        concreto_por_unidade=Decimal("1.000"),
        tipo_produto=TipoProduto.PRE_MOLDADO,
    )
    db_session.add_all([cliente, fornecedor, funcionario, produto])
    db_session.commit()
    for obj in (cliente, fornecedor, funcionario, produto):
        db_session.refresh(obj)

    financeiro = MovimentoFinanceiroService(
        MovimentoFinanceiroRepository(db_session)
    )
    financeiro.criar(
        MovimentoFinanceiroCreate(
            tipo=TipoMovimentoFinanceiro.VENDA,
            data_movimento=date(2026, 8, 1),
            valor=Decimal("10.00"),
            descricao="financeiro avulso dashboard",
        )
    )

    estoque = MovimentoEstoqueService(MovimentoEstoqueRepository(db_session))
    estoque.criar(
        MovimentoEstoqueCreate(
            data=date(2026, 8, 1),
            produto_id=produto.id,
            quantidade=Decimal("50"),
            tipo=TipoMovimentoEstoque.ENTRADA,
            observacao="estoque dashboard",
        )
    )

    compra = CompraConcretoService(CompraConcretoRepository(db_session)).criar(
        CompraConcretoCreate(
            fornecedor_id=fornecedor.id,
            data_compra=date(2026, 8, 2),
            nota_fiscal="NF-DASH",
            quantidade_comprada=Decimal("20.000"),
            quantidade_recebida=Decimal("20.000"),
            valor_total=Decimal("200.00"),
        )
    )
    db_session.add(
        FuncionarioValorProduto(
            funcionario_id=funcionario.id,
            produto_id=produto.id,
            valor=Decimal("5.00"),
        )
    )
    db_session.commit()

    ProducaoService(ProducaoRepository(db_session)).criar(
        ProducaoCreate(
            data=date(2026, 8, 3),
            funcionario_id=funcionario.id,
            produto_id=produto.id,
            compra_concreto_id=compra.id,
            quantidade_produzida=Decimal("4"),
        )
    )

    VendaService(VendaRepository(db_session)).criar(
        VendaCreate(
            cliente_id=cliente.id,
            data_venda=date(2026, 8, 4),
            numero="VD-DASH",
            valor_total=Decimal("0"),
            itens=[
                {
                    "produto_id": produto.id,
                    "quantidade": Decimal("3"),
                    "valor_unitario": Decimal("100.00"),
                }
            ],
        )
    )

    response = client_auth.get("/dashboard")
    assert response.status_code == 200
    dados = response.json()
    assert set(dados.keys()) == set(BLOCOS)

    # Financeiro: avulso VENDA 10 + compra 200 + produção 20 + venda 300
    assert dados["fluxo_financeiro"]["quantidade_lancamentos"] >= 4
    assert _d(dados["fluxo_financeiro"]["total_entradas"]) >= Decimal("310.00")
    assert _d(dados["fluxo_financeiro"]["total_saidas"]) >= Decimal("220.00")

    assert dados["comercial"]["quantidade_vendas"] == 1
    assert _d(dados["comercial"]["valor_total_vendas"]) == Decimal("300.00")

    assert dados["producao"]["quantidade_producoes"] == 1
    assert _d(dados["producao"]["quantidade_total_produzida"]) == Decimal("4")

    assert dados["estoque"]["quantidade_movimentos"] >= 3
    assert dados["estoque"]["produtos_movimentados"] >= 1

    assert _d(dados["executivo"]["faturamento_total"]) == Decimal("300.00")
    assert dados["executivo"]["quantidade_clientes_atendidos"] == 1
    assert dados["executivo"]["quantidade_produtos_movimentados"] >= 1
