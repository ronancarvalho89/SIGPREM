"""
Router de FuncionarioValorProduto — endpoints HTTP (COMMIT 0021).

Mapeia temporariamente exceções de domínio para HTTPException.
No futuro existirá um middleware/handler global de exceções.
"""

from typing import NoReturn

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import status
from sqlalchemy.orm import Session

from app.core.security import get_current_usuario
from app.database.database import get_db
from app.models.usuario import Usuario
from app.repositories.funcionario_valor_produto_repository import (
    FuncionarioValorProdutoRepository,
)
from app.schemas.funcionario_valor_produto import FuncionarioValorProdutoCreate
from app.schemas.funcionario_valor_produto import (
    FuncionarioValorProdutoResponse,
)
from app.schemas.funcionario_valor_produto import FuncionarioValorProdutoUpdate
from app.services.funcionario_valor_produto_service import (
    FuncionarioValorProdutoDuplicado,
)
from app.services.funcionario_valor_produto_service import (
    FuncionarioValorProdutoNaoEncontrado,
)
from app.services.funcionario_valor_produto_service import (
    FuncionarioValorProdutoService,
)


router = APIRouter(
    prefix="/funcionarios-valor-produto",
    tags=["Funcionários Valor Produto"],
)


def _get_service(db: Session) -> FuncionarioValorProdutoService:
    """Instancia o service com o repository."""
    return FuncionarioValorProdutoService(
        FuncionarioValorProdutoRepository(db)
    )


def _mapear_excecao(exc: Exception) -> NoReturn:
    """
    Converte exceções de domínio em HTTPException.

    Tratamento temporário na camada API até existir handler global.
    """
    if isinstance(exc, FuncionarioValorProdutoNaoEncontrado):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(exc, FuncionarioValorProdutoDuplicado):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    raise exc


@router.get("", response_model=list[FuncionarioValorProdutoResponse])
def listar(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> list[FuncionarioValorProdutoResponse]:
    """Lista valores ativos com paginação."""
    _ = usuario
    service = _get_service(db)
    return service.listar(skip=skip, limit=limit)


@router.get("/{registro_id}", response_model=FuncionarioValorProdutoResponse)
def buscar(
    registro_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> FuncionarioValorProdutoResponse:
    """Busca valor ativo pelo identificador."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.buscar_por_id(registro_id)
    except (
        FuncionarioValorProdutoNaoEncontrado,
        FuncionarioValorProdutoDuplicado,
    ) as exc:
        _mapear_excecao(exc)


@router.post(
    "",
    response_model=FuncionarioValorProdutoResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar(
    dados: FuncionarioValorProdutoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> FuncionarioValorProdutoResponse:
    """Cadastra um novo valor por funcionário/produto."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.criar(dados)
    except (
        FuncionarioValorProdutoNaoEncontrado,
        FuncionarioValorProdutoDuplicado,
    ) as exc:
        _mapear_excecao(exc)


@router.put("/{registro_id}", response_model=FuncionarioValorProdutoResponse)
def atualizar(
    registro_id: int,
    dados: FuncionarioValorProdutoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> FuncionarioValorProdutoResponse:
    """Atualiza campos informados de um registro ativo."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.atualizar(registro_id, dados)
    except (
        FuncionarioValorProdutoNaoEncontrado,
        FuncionarioValorProdutoDuplicado,
    ) as exc:
        _mapear_excecao(exc)


@router.delete(
    "/{registro_id}",
    response_model=FuncionarioValorProdutoResponse,
)
def excluir(
    registro_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> FuncionarioValorProdutoResponse:
    """Exclusão lógica do registro (ativo = False)."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.excluir(registro_id)
    except (
        FuncionarioValorProdutoNaoEncontrado,
        FuncionarioValorProdutoDuplicado,
    ) as exc:
        _mapear_excecao(exc)
