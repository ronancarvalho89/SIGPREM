"""
Router de Movimentos de Estoque — endpoints HTTP (COMMIT 0017).

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
from app.repositories.movimento_estoque_repository import (
    MovimentoEstoqueRepository,
)
from app.schemas.movimento_estoque import MovimentoEstoqueCreate
from app.schemas.movimento_estoque import MovimentoEstoqueResponse
from app.schemas.movimento_estoque import MovimentoEstoqueUpdate
from app.services.movimento_estoque_service import MovimentoEstoqueNaoEncontrado
from app.services.movimento_estoque_service import MovimentoEstoqueService


router = APIRouter(
    prefix="/movimentos-estoque",
    tags=["Movimentos de Estoque"],
)


def _get_service(db: Session) -> MovimentoEstoqueService:
    """Instancia o service de movimento de estoque com o repository."""
    return MovimentoEstoqueService(MovimentoEstoqueRepository(db))


def _mapear_excecao(exc: Exception) -> NoReturn:
    """
    Converte exceções de domínio em HTTPException.

    Tratamento temporário na camada API até existir handler global.
    """
    if isinstance(exc, MovimentoEstoqueNaoEncontrado):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    raise exc


@router.get("", response_model=list[MovimentoEstoqueResponse])
def listar(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> list[MovimentoEstoqueResponse]:
    """Lista movimentos ativos com paginação (data DESC)."""
    _ = usuario
    service = _get_service(db)
    return service.listar(skip=skip, limit=limit)


@router.get("/{movimento_id}", response_model=MovimentoEstoqueResponse)
def buscar(
    movimento_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> MovimentoEstoqueResponse:
    """Busca movimento ativo pelo identificador."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.buscar_por_id(movimento_id)
    except MovimentoEstoqueNaoEncontrado as exc:
        _mapear_excecao(exc)


@router.post(
    "",
    response_model=MovimentoEstoqueResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar(
    dados: MovimentoEstoqueCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> MovimentoEstoqueResponse:
    """Cadastra um novo movimento de estoque."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.criar(dados)
    except MovimentoEstoqueNaoEncontrado as exc:
        _mapear_excecao(exc)


@router.put("/{movimento_id}", response_model=MovimentoEstoqueResponse)
def atualizar(
    movimento_id: int,
    dados: MovimentoEstoqueUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> MovimentoEstoqueResponse:
    """Atualiza campos informados de um movimento ativo."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.atualizar(movimento_id, dados)
    except MovimentoEstoqueNaoEncontrado as exc:
        _mapear_excecao(exc)


@router.delete("/{movimento_id}", response_model=MovimentoEstoqueResponse)
def excluir(
    movimento_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> MovimentoEstoqueResponse:
    """Exclusão lógica do movimento (ativo = False)."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.excluir(movimento_id)
    except MovimentoEstoqueNaoEncontrado as exc:
        _mapear_excecao(exc)
