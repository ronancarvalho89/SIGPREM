"""
Testes do módulo Produção (EPIC 003 — ETAPA 5).
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
from app.models.fornecedor import Fornecedor
from app.models.funcionario import Funcionario
from app.models.funcionario_valor_produto import FuncionarioValorProduto
from app.models.movimento_estoque import MovimentoEstoque
from app.models.movimento_estoque import TipoMovimentoEstoque
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
from app.schemas.producao import ProducaoCreate
from app.schemas.producao import ProducaoUpdate
from app.services.compra_concreto_service import CompraConcretoService
from app.services.movimento_estoque_service import MovimentoEstoqueService
from app.services.producao_service import ProducaoDadosInvalidos
from app.services.producao_service import ProducaoJaEfetivada
from app.services.producao_service import ProducaoNaoEncontrada
from app.services.producao_service import ProducaoService
from app.services.producao_service import SaldoConcretoInsuficiente
from app.services.producao_service import ValorMaoObraNaoCadastrado


@pytest.fixture()
def producao_service(db_session: Session) -> ProducaoService:
    """ProducaoService na sessão de teste."""
    return ProducaoService(ProducaoRepository(db_session))


@pytest.fixture()
def estoque_service(db_session: Session) -> MovimentoEstoqueService:
    """Somente para leitura de saldo após produção."""
    return MovimentoEstoqueService(MovimentoEstoqueRepository(db_session))


@pytest.fixture()
def cenario(db_session: Session) -> dict[str, Any]:
    """
    Cenário base: compra saldo 100, produto concreto/un=1,
    funcionário com valor mão de obra 10.00.
    """
    fornecedor = Fornecedor(
        razao_social="Fornecedor Produção",
        cpf_cnpj="99887766000155",
        telefone="",
        email="",
        observacao="",
    )
    funcionario = Funcionario(
        nome="Produtor Teste",
        cpf="55566677788",
        telefone="",
        data_admissao=date(2026, 1, 1),
    )
    produto = Produto(
        codigo="PROD-A",
        descricao="Produto Produção A",
        categoria=CategoriaProduto.BLOQUETE,
        modelo="A",
        unidade=UnidadeProduto.UN,
        concreto_por_unidade=Decimal("1.000"),
        tipo_produto=TipoProduto.PRE_MOLDADO,
    )
    produto_b = Produto(
        codigo="PROD-B",
        descricao="Produto Produção B",
        categoria=CategoriaProduto.BLOQUETE,
        modelo="B",
        unidade=UnidadeProduto.UN,
        concreto_por_unidade=Decimal("1.000"),
        tipo_produto=TipoProduto.PRE_MOLDADO,
    )
    db_session.add_all([fornecedor, funcionario, produto, produto_b])
    db_session.commit()
    db_session.refresh(fornecedor)
    db_session.refresh(funcionario)
    db_session.refresh(produto)
    db_session.refresh(produto_b)

    compra_service = CompraConcretoService(CompraConcretoRepository(db_session))
    compra = compra_service.criar(
        CompraConcretoCreate(
            fornecedor_id=fornecedor.id,
            data_compra=date(2026, 8, 1),
            nota_fiscal="NF-PROD-100",
            quantidade_comprada=Decimal("100.000"),
            quantidade_recebida=Decimal("100.000"),
            valor_total=Decimal("5000.00"),
            observacao="cenario producao",
        )
    )

    valor_a = FuncionarioValorProduto(
        funcionario_id=funcionario.id,
        produto_id=produto.id,
        valor=Decimal("10.00"),
    )
    valor_b = FuncionarioValorProduto(
        funcionario_id=funcionario.id,
        produto_id=produto_b.id,
        valor=Decimal("7.00"),
    )
    db_session.add_all([valor_a, valor_b])
    db_session.commit()

    return {
        "fornecedor": fornecedor,
        "funcionario": funcionario,
        "produto": produto,
        "produto_b": produto_b,
        "compra": compra,
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


def _payload(
    cenario: dict[str, Any],
    *,
    quantidade: Decimal,
    produto: Produto | None = None,
    observacao: str = "producao teste",
) -> ProducaoCreate:
    item = produto or cenario["produto"]
    return ProducaoCreate(
        data=date(2026, 8, 12),
        funcionario_id=cenario["funcionario"].id,
        produto_id=item.id,
        compra_concreto_id=cenario["compra"].id,
        quantidade_produzida=quantidade,
        observacao=observacao,
    )


def _movimentos_estoque_producao(
    db_session: Session,
    producao_id: int,
) -> list[MovimentoEstoque]:
    return (
        db_session.query(MovimentoEstoque)
        .filter(MovimentoEstoque.producao_id == producao_id)
        .all()
    )


def _movimentos_financeiros_producao(
    db_session: Session,
    producao_id: int,
) -> list[MovimentoFinanceiro]:
    return (
        db_session.query(MovimentoFinanceiro)
        .filter(
            MovimentoFinanceiro.tipo == TipoMovimentoFinanceiro.PRODUCAO,
            MovimentoFinanceiro.observacao.contains(f"Produção {producao_id}"),
        )
        .all()
    )


# ---------------------------------------------------------------------------
# 2. Criação + efeitos
# ---------------------------------------------------------------------------


def test_criar_producao_efeitos_completos(
    producao_service: ProducaoService,
    estoque_service: MovimentoEstoqueService,
    cenario: dict[str, Any],
    db_session: Session,
) -> None:
    producao = producao_service.criar(_payload(cenario, quantidade=Decimal("30")))

    assert producao.id is not None
    assert producao.produto_id == cenario["produto"].id
    assert producao.funcionario_id == cenario["funcionario"].id
    assert Decimal(str(producao.quantidade_produzida)) == Decimal("30")
    assert Decimal(str(producao.concreto_consumido)) == Decimal("30.000")
    assert Decimal(str(producao.valor_producao)) == Decimal("300.00")

    db_session.refresh(cenario["compra"])
    assert Decimal(str(cenario["compra"].saldo)) == Decimal("70.000")

    estoques = _movimentos_estoque_producao(db_session, producao.id)
    assert len(estoques) == 1
    assert estoques[0].tipo == TipoMovimentoEstoque.ENTRADA
    assert estoques[0].produto_id == cenario["produto"].id
    assert Decimal(str(estoques[0].quantidade)) == Decimal("30")
    assert estoque_service.saldo_produto(cenario["produto"].id) == Decimal("30")

    financeiros = _movimentos_financeiros_producao(db_session, producao.id)
    assert len(financeiros) == 1
    assert Decimal(str(financeiros[0].valor)) == Decimal("300.00")
    assert financeiros[0].descricao == "Custo de produção"

    auditorias = (
        db_session.query(Auditoria)
        .filter(
            Auditoria.modulo == "producao",
            Auditoria.acao == "criar",
            Auditoria.entidade == "Producao",
            Auditoria.entidade_id == producao.id,
        )
        .all()
    )
    assert len(auditorias) == 1
    assert auditorias[0].usuario_id is None  # chamada direta sem usuário


# ---------------------------------------------------------------------------
# 3–4. Consumo de concreto / saldo insuficiente
# ---------------------------------------------------------------------------


def test_consumo_parcial_e_total_do_saldo(
    producao_service: ProducaoService,
    cenario: dict[str, Any],
    db_session: Session,
) -> None:
    producao_service.criar(_payload(cenario, quantidade=Decimal("30")))
    db_session.refresh(cenario["compra"])
    assert Decimal(str(cenario["compra"].saldo)) == Decimal("70.000")

    producao_service.criar(_payload(cenario, quantidade=Decimal("70")))
    db_session.refresh(cenario["compra"])
    assert Decimal(str(cenario["compra"].saldo)) == Decimal("0.000")


def test_saldo_insuficiente_nao_altera_estado(
    producao_service: ProducaoService,
    cenario: dict[str, Any],
    db_session: Session,
) -> None:
    with pytest.raises(SaldoConcretoInsuficiente):
        producao_service.criar(_payload(cenario, quantidade=Decimal("101")))

    db_session.refresh(cenario["compra"])
    assert Decimal(str(cenario["compra"].saldo)) == Decimal("100.000")
    assert db_session.query(Producao).count() == 0
    assert db_session.query(MovimentoEstoque).count() == 0
    assert (
        db_session.query(MovimentoFinanceiro)
        .filter(MovimentoFinanceiro.tipo == TipoMovimentoFinanceiro.PRODUCAO)
        .count()
        == 0
    )


# ---------------------------------------------------------------------------
# 13. Funcionário × Produto
# ---------------------------------------------------------------------------


def test_sem_valor_mao_obra(
    producao_service: ProducaoService,
    cenario: dict[str, Any],
    db_session: Session,
) -> None:
    funcionario_sem_valor = Funcionario(
        nome="Sem Valor",
        cpf="12121212121",
        telefone="",
        data_admissao=date(2026, 2, 1),
    )
    db_session.add(funcionario_sem_valor)
    db_session.commit()
    db_session.refresh(funcionario_sem_valor)

    with pytest.raises(ValorMaoObraNaoCadastrado):
        producao_service.criar(
            ProducaoCreate(
                data=date(2026, 8, 12),
                funcionario_id=funcionario_sem_valor.id,
                produto_id=cenario["produto"].id,
                compra_concreto_id=cenario["compra"].id,
                quantidade_produzida=Decimal("1"),
                observacao="",
            )
        )

    db_session.refresh(cenario["compra"])
    assert Decimal(str(cenario["compra"].saldo)) == Decimal("100.000")


def test_compra_ou_produto_inexistente(
    producao_service: ProducaoService,
    cenario: dict[str, Any],
) -> None:
    with pytest.raises(ProducaoDadosInvalidos):
        producao_service.criar(
            ProducaoCreate(
                data=date(2026, 8, 12),
                funcionario_id=cenario["funcionario"].id,
                produto_id=cenario["produto"].id,
                compra_concreto_id=99999,
                quantidade_produzida=Decimal("1"),
                observacao="",
            )
        )


# ---------------------------------------------------------------------------
# 9. Rollback em falha no financeiro
# ---------------------------------------------------------------------------


def test_rollback_quando_financeiro_falha(
    producao_service: ProducaoService,
    cenario: dict[str, Any],
    db_session: Session,
) -> None:
    class FinanceiroQueFalha:
        def registrar(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("falha financeira na producao")

    producao_service.financeiro_service = FinanceiroQueFalha()  # type: ignore[assignment]

    with pytest.raises(RuntimeError, match="falha financeira"):
        producao_service.criar(_payload(cenario, quantidade=Decimal("10")))

    db_session.refresh(cenario["compra"])
    assert Decimal(str(cenario["compra"].saldo)) == Decimal("100.000")
    assert db_session.query(Producao).count() == 0
    assert db_session.query(MovimentoEstoque).count() == 0
    assert (
        db_session.query(MovimentoFinanceiro)
        .filter(MovimentoFinanceiro.tipo == TipoMovimentoFinanceiro.PRODUCAO)
        .count()
        == 0
    )
    assert (
        db_session.query(Auditoria)
        .filter(Auditoria.modulo == "producao", Auditoria.acao == "criar")
        .count()
        == 0
    )


# ---------------------------------------------------------------------------
# 14. Isolamento por produto
# ---------------------------------------------------------------------------


def test_efeitos_isolados_por_produto(
    producao_service: ProducaoService,
    estoque_service: MovimentoEstoqueService,
    cenario: dict[str, Any],
) -> None:
    producao_service.criar(
        _payload(cenario, quantidade=Decimal("10"), produto=cenario["produto"])
    )
    producao_service.criar(
        _payload(
            cenario,
            quantidade=Decimal("5"),
            produto=cenario["produto_b"],
        )
    )

    assert estoque_service.saldo_produto(cenario["produto"].id) == Decimal("10")
    assert estoque_service.saldo_produto(cenario["produto_b"].id) == Decimal("5")


# ---------------------------------------------------------------------------
# 10–11. Update / exclusão — Política A (Pacote 4.6.2)
# ---------------------------------------------------------------------------


def test_atualizar_producao_efetivada_bloqueado(
    producao_service: ProducaoService,
    estoque_service: MovimentoEstoqueService,
    cenario: dict[str, Any],
    db_session: Session,
) -> None:
    producao = producao_service.criar(_payload(cenario, quantidade=Decimal("20")))
    db_session.refresh(cenario["compra"])
    saldo_compra = Decimal(str(cenario["compra"].saldo))
    saldo_estoque = estoque_service.saldo_produto(cenario["produto"].id)
    valor_fin = Decimal(
        str(_movimentos_financeiros_producao(db_session, producao.id)[0].valor)
    )
    observacao_antes = producao.observacao
    mov_estoque_antes = db_session.query(MovimentoEstoque).count()
    mov_fin_antes = db_session.query(MovimentoFinanceiro).count()
    aud_antes = db_session.query(Auditoria).count()

    with pytest.raises(ProducaoJaEfetivada):
        producao_service.atualizar(
            producao.id,
            ProducaoUpdate(observacao="somente observacao"),
        )

    db_session.refresh(producao)
    db_session.refresh(cenario["compra"])
    assert producao.ativo is True
    assert producao.observacao == observacao_antes
    assert Decimal(str(cenario["compra"].saldo)) == saldo_compra
    assert estoque_service.saldo_produto(cenario["produto"].id) == saldo_estoque
    assert Decimal(
        str(_movimentos_financeiros_producao(db_session, producao.id)[0].valor)
    ) == valor_fin
    assert db_session.query(MovimentoEstoque).count() == mov_estoque_antes
    assert db_session.query(MovimentoFinanceiro).count() == mov_fin_antes
    assert db_session.query(Auditoria).count() == aud_antes


def test_excluir_producao_efetivada_bloqueado(
    producao_service: ProducaoService,
    estoque_service: MovimentoEstoqueService,
    cenario: dict[str, Any],
    db_session: Session,
) -> None:
    producao = producao_service.criar(_payload(cenario, quantidade=Decimal("15")))
    db_session.refresh(cenario["compra"])
    saldo_apos = Decimal(str(cenario["compra"].saldo))
    mov_estoque_antes = db_session.query(MovimentoEstoque).count()
    mov_fin_antes = db_session.query(MovimentoFinanceiro).count()
    aud_antes = db_session.query(Auditoria).count()

    with pytest.raises(ProducaoJaEfetivada):
        producao_service.excluir(producao.id)

    db_session.refresh(producao)
    db_session.refresh(cenario["compra"])
    assert producao.ativo is True
    assert producao_service.buscar_por_id(producao.id).id == producao.id
    assert Decimal(str(cenario["compra"].saldo)) == saldo_apos
    assert estoque_service.saldo_produto(cenario["produto"].id) == Decimal("15")
    assert len(_movimentos_financeiros_producao(db_session, producao.id)) == 1
    assert db_session.query(MovimentoEstoque).count() == mov_estoque_antes
    assert db_session.query(MovimentoFinanceiro).count() == mov_fin_antes
    assert db_session.query(Auditoria).count() == aud_antes
    assert (
        db_session.query(Auditoria)
        .filter(
            Auditoria.modulo == "producao",
            Auditoria.acao == "inativar",
            Auditoria.entidade_id == producao.id,
        )
        .count()
        == 0
    )


# ---------------------------------------------------------------------------
# 12. API
# ---------------------------------------------------------------------------


def test_api_producao_exige_autenticacao(client_anon: TestClient) -> None:
    assert client_anon.get("/producao").status_code == 401


def test_api_criar_listar_relatorio_update_delete_bloqueados(
    client_auth: TestClient,
    cenario: dict[str, Any],
    db_session: Session,
    estoque_service: MovimentoEstoqueService,
) -> None:
    criar = client_auth.post(
        "/producao",
        json={
            "data": "2026-08-12",
            "funcionario_id": cenario["funcionario"].id,
            "produto_id": cenario["produto"].id,
            "compra_concreto_id": cenario["compra"].id,
            "quantidade_produzida": "8",
            "observacao": "api",
        },
    )
    assert criar.status_code == 201
    body = criar.json()
    assert Decimal(str(body["concreto_consumido"])) == Decimal("8.000")
    producao_id = body["id"]

    assert client_auth.get("/producao").status_code == 200
    assert len(client_auth.get("/producao").json()) == 1
    assert client_auth.get(f"/producao/{producao_id}").status_code == 200

    relatorio = client_auth.get(
        "/producao/relatorio/periodo",
        params={
            "data_inicial": "2026-08-01",
            "data_final": "2026-08-31",
        },
    )
    assert relatorio.status_code == 200
    assert relatorio.json()["quantidade_producoes"] == 1

    db_session.refresh(cenario["compra"])
    saldo_compra = Decimal(str(cenario["compra"].saldo))
    saldo_estoque = estoque_service.saldo_produto(cenario["produto"].id)
    fin_antes = len(_movimentos_financeiros_producao(db_session, producao_id))
    aud_antes = db_session.query(Auditoria).count()

    atualizar = client_auth.put(
        f"/producao/{producao_id}",
        json={"observacao": "api atualizada"},
    )
    assert atualizar.status_code == 400
    assert "efetivada" in atualizar.json()["detail"].lower()

    excluir = client_auth.delete(f"/producao/{producao_id}")
    assert excluir.status_code == 400
    assert "efetivada" in excluir.json()["detail"].lower()

    detalhe = client_auth.get(f"/producao/{producao_id}")
    assert detalhe.status_code == 200
    assert detalhe.json()["ativo"] is True
    assert detalhe.json()["observacao"] == "api"
    db_session.refresh(cenario["compra"])
    assert Decimal(str(cenario["compra"].saldo)) == saldo_compra
    assert estoque_service.saldo_produto(cenario["produto"].id) == saldo_estoque
    assert (
        len(_movimentos_financeiros_producao(db_session, producao_id))
        == fin_antes
    )
    assert db_session.query(Auditoria).count() == aud_antes


def test_api_auditoria_recebe_usuario_id(
    client_auth: TestClient,
    cenario: dict[str, Any],
    db_session: Session,
    usuario: Usuario,
) -> None:
    response = client_auth.post(
        "/producao",
        json={
            "data": "2026-08-12",
            "funcionario_id": cenario["funcionario"].id,
            "produto_id": cenario["produto"].id,
            "compra_concreto_id": cenario["compra"].id,
            "quantidade_produzida": "1",
            "observacao": "",
        },
    )
    assert response.status_code == 201
    producao_id = response.json()["id"]

    auditoria = (
        db_session.query(Auditoria)
        .filter(
            Auditoria.modulo == "producao",
            Auditoria.acao == "criar",
            Auditoria.entidade_id == producao_id,
        )
        .one()
    )
    assert auditoria.usuario_id == usuario.id


def test_api_saldo_insuficiente(
    client_auth: TestClient,
    cenario: dict[str, Any],
) -> None:
    response = client_auth.post(
        "/producao",
        json={
            "data": "2026-08-12",
            "funcionario_id": cenario["funcionario"].id,
            "produto_id": cenario["produto"].id,
            "compra_concreto_id": cenario["compra"].id,
            "quantidade_produzida": "200",
            "observacao": "",
        },
    )
    assert response.status_code == 400
    assert "Saldo insuficiente" in response.json()["detail"]


def test_api_valor_mao_obra_nao_cadastrado_retorna_400(
    client_auth: TestClient,
    cenario: dict[str, Any],
    db_session: Session,
) -> None:
    """ValorMaoObraNaoCadastrado → HTTP 400 (Pacote 4.4)."""
    funcionario = Funcionario(
        nome="Sem MO API",
        cpf="34343434343",
        telefone="",
        data_admissao=date(2026, 3, 1),
    )
    db_session.add(funcionario)
    db_session.commit()
    db_session.refresh(funcionario)

    response = client_auth.post(
        "/producao",
        json={
            "data": "2026-08-12",
            "funcionario_id": funcionario.id,
            "produto_id": cenario["produto"].id,
            "compra_concreto_id": cenario["compra"].id,
            "quantidade_produzida": "1",
            "observacao": "",
        },
    )
    assert response.status_code == 400
    assert "mão de obra" in response.json()["detail"]


def test_api_producao_dados_invalidos_retorna_400(
    client_auth: TestClient,
    cenario: dict[str, Any],
) -> None:
    response = client_auth.post(
        "/producao",
        json={
            "data": "2026-08-12",
            "funcionario_id": cenario["funcionario"].id,
            "produto_id": cenario["produto"].id,
            "compra_concreto_id": 999999,
            "quantidade_produzida": "1",
            "observacao": "",
        },
    )
    assert response.status_code == 400
    assert "Compra de concreto não encontrada" in response.json()["detail"]


def test_api_erro_inesperado_nao_mascarado(
    client_auth: TestClient,
    cenario: dict[str, Any],
) -> None:
    """Erros internos não devem virar HTTP 400 genérico."""
    from app.services.producao_service import ProducaoService

    original = ProducaoService.criar

    def _falha(self, *args, **kwargs):
        raise RuntimeError("falha interna producao")

    ProducaoService.criar = _falha  # type: ignore[method-assign]
    try:
        with pytest.raises(RuntimeError, match="falha interna producao"):
            client_auth.post(
                "/producao",
                json={
                    "data": "2026-08-12",
                    "funcionario_id": cenario["funcionario"].id,
                    "produto_id": cenario["produto"].id,
                    "compra_concreto_id": cenario["compra"].id,
                    "quantidade_produzida": "1",
                    "observacao": "",
                },
            )
    finally:
        ProducaoService.criar = original  # type: ignore[method-assign]
