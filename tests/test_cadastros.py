"""
Testes estratégicos de Cadastros (EPIC 003 — ETAPA 7).
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models.fornecedor import Fornecedor
from app.models.funcionario import Funcionario
from app.models.produto import CategoriaProduto
from app.models.produto import Produto
from app.models.produto import TipoProduto
from app.models.produto import UnidadeProduto
from app.models.producao import Producao
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.fornecedor_repository import FornecedorRepository
from app.repositories.funcionario_repository import FuncionarioRepository
from app.repositories.funcionario_valor_produto_repository import (
    FuncionarioValorProdutoRepository,
)
from app.repositories.produto_repository import ProdutoRepository
from app.schemas.cliente import ClienteCreate
from app.schemas.fornecedor import FornecedorCreate
from app.schemas.funcionario import FuncionarioCreate
from app.schemas.funcionario_valor_produto import FuncionarioValorProdutoCreate
from app.schemas.produto import ProdutoCreate
from app.schemas.produto import ProdutoUpdate
from app.services.cliente_service import ClienteDuplicado
from app.services.cliente_service import ClienteService
from app.services.fornecedor_service import FornecedorDuplicado
from app.services.fornecedor_service import FornecedorService
from app.services.funcionario_service import FuncionarioDuplicado
from app.services.funcionario_service import FuncionarioService
from app.services.funcionario_valor_produto_service import (
    FuncionarioValorProdutoNaoEncontrado,
)
from app.services.funcionario_valor_produto_service import (
    FuncionarioValorProdutoService,
)
from app.services.produto_service import ProdutoDuplicado
from app.services.produto_service import ProdutoService
from app.services.produto_service import UnidadeNaoPodeSerAlterada


@pytest.fixture()
def produto_service(db_session: Session) -> ProdutoService:
    return ProdutoService(ProdutoRepository(db_session))


@pytest.fixture()
def cliente_service(db_session: Session) -> ClienteService:
    return ClienteService(ClienteRepository(db_session))


@pytest.fixture()
def fornecedor_service(db_session: Session) -> FornecedorService:
    return FornecedorService(FornecedorRepository(db_session))


@pytest.fixture()
def funcionario_service(db_session: Session) -> FuncionarioService:
    return FuncionarioService(FuncionarioRepository(db_session))


@pytest.fixture()
def valor_service(db_session: Session) -> FuncionarioValorProdutoService:
    return FuncionarioValorProdutoService(
        FuncionarioValorProdutoRepository(db_session)
    )


def _produto(
    *,
    codigo: str = "CAD-1",
    descricao: str = "Produto Cadastro",
    unidade: UnidadeProduto = UnidadeProduto.UN,
) -> ProdutoCreate:
    return ProdutoCreate(
        codigo=codigo,
        descricao=descricao,
        categoria=CategoriaProduto.BLOQUETE,
        modelo="M1",
        unidade=unidade,
        concreto_por_unidade=Decimal("0"),
        tipo_produto=TipoProduto.PRE_MOLDADO,
    )


# ---------------------------------------------------------------------------
# Produto
# ---------------------------------------------------------------------------


def test_produto_criar_e_unicidade(
    produto_service: ProdutoService,
) -> None:
    produto = produto_service.criar(_produto())
    assert produto.id is not None
    assert produto.categoria == CategoriaProduto.BLOQUETE
    assert produto.unidade == UnidadeProduto.UN

    with pytest.raises(ProdutoDuplicado):
        produto_service.criar(_produto(codigo="CAD-1", descricao="Outra"))

    with pytest.raises(ProdutoDuplicado):
        produto_service.criar(
            _produto(codigo="CAD-2", descricao="Produto Cadastro")
        )


def test_produto_update_schema_nao_expoe_categoria() -> None:
    assert "categoria" not in ProdutoUpdate.model_fields
    assert "codigo" not in ProdutoUpdate.model_fields


def test_produto_unidade_bloqueada_com_producao(
    produto_service: ProdutoService,
    db_session: Session,
) -> None:
    produto = produto_service.criar(_produto(codigo="CAD-UN", descricao="Com prod"))
    funcionario = Funcionario(
        nome="Func Cad",
        cpf="11122233300",
        data_admissao=date(2026, 1, 1),
    )
    fornecedor = Fornecedor(
        razao_social="Forn Cad",
        cpf_cnpj="12312312300111",
    )
    db_session.add_all([funcionario, fornecedor])
    db_session.commit()
    db_session.refresh(funcionario)
    db_session.refresh(fornecedor)

    from app.models.compra_concreto import CompraConcreto

    compra = CompraConcreto(
        fornecedor_id=fornecedor.id,
        data_compra=date(2026, 8, 1),
        nota_fiscal="NF-CAD",
        quantidade_comprada=Decimal("10"),
        quantidade_recebida=Decimal("10"),
        saldo=Decimal("10"),
        valor_total=Decimal("100"),
    )
    db_session.add(compra)
    db_session.commit()
    db_session.refresh(compra)

    producao = Producao(
        data=date(2026, 8, 2),
        funcionario_id=funcionario.id,
        produto_id=produto.id,
        compra_concreto_id=compra.id,
        quantidade_produzida=Decimal("1"),
        concreto_consumido=Decimal("0"),
        valor_producao=Decimal("1"),
    )
    db_session.add(producao)
    db_session.commit()

    with pytest.raises(UnidadeNaoPodeSerAlterada):
        produto_service.atualizar(
            produto.id,
            ProdutoUpdate(unidade=UnidadeProduto.M2),
        )


# ---------------------------------------------------------------------------
# Cliente / Fornecedor / Funcionário
# ---------------------------------------------------------------------------


def test_cliente_criar_consultar_unicidade(
    cliente_service: ClienteService,
) -> None:
    cliente = cliente_service.criar(
        ClienteCreate(
            razao_social="Cliente Cad",
            cpf_cnpj="11111111000111",
        )
    )
    assert cliente_service.buscar_por_id(cliente.id).id == cliente.id

    with pytest.raises(ClienteDuplicado):
        cliente_service.criar(
            ClienteCreate(
                razao_social="Outro",
                cpf_cnpj="11111111000111",
            )
        )


def test_fornecedor_criar_consultar_unicidade(
    fornecedor_service: FornecedorService,
) -> None:
    fornecedor = fornecedor_service.criar(
        FornecedorCreate(
            razao_social="Fornecedor Cad",
            cpf_cnpj="22222222000122",
        )
    )
    assert fornecedor_service.buscar_por_id(fornecedor.id).id == fornecedor.id

    with pytest.raises(FornecedorDuplicado):
        fornecedor_service.criar(
            FornecedorCreate(
                razao_social="Outro Forn",
                cpf_cnpj="22222222000122",
            )
        )


def test_funcionario_criar_consultar_unicidade(
    funcionario_service: FuncionarioService,
) -> None:
    funcionario = funcionario_service.criar(
        FuncionarioCreate(
            nome="Funcionário Cad",
            cpf="12345678901",
            data_admissao=date(2026, 1, 1),
        )
    )
    assert funcionario_service.buscar_por_id(funcionario.id).nome == (
        "Funcionário Cad"
    )

    with pytest.raises(FuncionarioDuplicado):
        funcionario_service.criar(
            FuncionarioCreate(
                nome="Outro",
                cpf="12345678901",
                data_admissao=date(2026, 2, 1),
            )
        )


# ---------------------------------------------------------------------------
# Funcionário × Produto
# ---------------------------------------------------------------------------


def test_funcionario_valor_produto_criar_consultar_inexistente(
    funcionario_service: FuncionarioService,
    produto_service: ProdutoService,
    valor_service: FuncionarioValorProdutoService,
) -> None:
    funcionario = funcionario_service.criar(
        FuncionarioCreate(
            nome="MO Cad",
            cpf="98765432100",
            data_admissao=date(2026, 1, 1),
        )
    )
    produto = produto_service.criar(
        _produto(codigo="CAD-MO", descricao="Produto MO")
    )

    valor = valor_service.criar(
        FuncionarioValorProdutoCreate(
            funcionario_id=funcionario.id,
            produto_id=produto.id,
            valor=Decimal("12.50"),
        )
    )
    assert Decimal(str(valor.valor)) == Decimal("12.50")
    assert valor_service.buscar_por_id(valor.id).id == valor.id

    with pytest.raises(FuncionarioValorProdutoNaoEncontrado):
        valor_service.buscar_por_id(99999)


# ---------------------------------------------------------------------------
# Soft delete representativo
# ---------------------------------------------------------------------------


def test_soft_delete_cliente(
    cliente_service: ClienteService,
    db_session: Session,
) -> None:
    from app.models.cliente import Cliente

    cliente = cliente_service.criar(
        ClienteCreate(
            razao_social="Cliente Soft",
            cpf_cnpj="33333333000133",
        )
    )
    inativado = cliente_service.excluir(cliente.id)

    assert inativado.ativo is False
    assert cliente.id not in {c.id for c in cliente_service.listar()}
    assert (
        db_session.query(Cliente)
        .filter(Cliente.id == cliente.id)
        .one()
        .ativo
        is False
    )
