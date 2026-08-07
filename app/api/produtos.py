"""
Router de Produtos — endpoints HTTP do cadastro (COMMIT 0003).

Mapeia temporariamente exceções de domínio para HTTPException.
No futuro existirá um middleware/handler global de exceções.

TODO(SIGPREM-001): futura migração Alembic.
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
from app.repositories.produto_repository import ProdutoRepository
from app.schemas.produto import ProdutoCreate
from app.schemas.produto import ProdutoResponse
from app.schemas.produto import ProdutoUpdate
from app.services.produto_service import CategoriaNaoPodeSerAlterada
from app.services.produto_service import ProdutoDuplicado
from app.services.produto_service import ProdutoNaoEncontrado
from app.services.produto_service import ProdutoService
from app.services.produto_service import UnidadeNaoPodeSerAlterada


router = APIRouter(
    prefix="/produtos",
    tags=["Produtos"],
)


def _get_service(db: Session) -> ProdutoService:
    """Instancia o service de produto com o repository."""
    return ProdutoService(ProdutoRepository(db))


def _mapear_excecao(exc: Exception) -> NoReturn:
    """
    Converte exceções de domínio em HTTPException.

    Tratamento temporário na camada API até existir handler global.
    """
    if isinstance(exc, ProdutoNaoEncontrado):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(exc, ProdutoDuplicado):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if isinstance(exc, CategoriaNaoPodeSerAlterada):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if isinstance(exc, UnidadeNaoPodeSerAlterada):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    raise exc


@router.get("", response_model=list[ProdutoResponse])
def listar(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> list[ProdutoResponse]:
    """Lista produtos ativos com paginação (codigo ASC)."""
    _ = usuario
    service = _get_service(db)
    return service.listar(skip=skip, limit=limit)


@router.get("/{produto_id}", response_model=ProdutoResponse)
def buscar(
    produto_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ProdutoResponse:
    """Busca produto ativo pelo identificador."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.buscar_por_id(produto_id)
    except (
        ProdutoNaoEncontrado,
        ProdutoDuplicado,
        CategoriaNaoPodeSerAlterada,
        UnidadeNaoPodeSerAlterada,
    ) as exc:
        _mapear_excecao(exc)


@router.post(
    "",
    response_model=ProdutoResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar(
    dados: ProdutoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ProdutoResponse:
    """Cadastra um novo produto."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.criar(dados)
    except (
        ProdutoNaoEncontrado,
        ProdutoDuplicado,
        CategoriaNaoPodeSerAlterada,
        UnidadeNaoPodeSerAlterada,
    ) as exc:
        _mapear_excecao(exc)


@router.put("/{produto_id}", response_model=ProdutoResponse)
def atualizar(
    produto_id: int,
    dados: ProdutoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ProdutoResponse:
    """Atualiza campos permitidos de um produto ativo."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.atualizar(produto_id, dados)
    except (
        ProdutoNaoEncontrado,
        ProdutoDuplicado,
        CategoriaNaoPodeSerAlterada,
        UnidadeNaoPodeSerAlterada,
    ) as exc:
        _mapear_excecao(exc)


@router.delete("/{produto_id}", response_model=ProdutoResponse)
def excluir(
    produto_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ProdutoResponse:
    """Exclusão lógica do produto (ativo = False)."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.excluir(produto_id)
    except (
        ProdutoNaoEncontrado,
        ProdutoDuplicado,
        CategoriaNaoPodeSerAlterada,
        UnidadeNaoPodeSerAlterada,
    ) as exc:
        _mapear_excecao(exc)
