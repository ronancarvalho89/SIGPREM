"""
Router de Movimentos Financeiros — endpoints HTTP (COMMIT 0025).

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
from app.repositories.movimento_financeiro_repository import (
    MovimentoFinanceiroRepository,
)
from app.schemas.movimento_financeiro import MovimentoFinanceiroCreate
from app.schemas.movimento_financeiro import MovimentoFinanceiroResponse
from app.schemas.movimento_financeiro import MovimentoFinanceiroUpdate
from app.services.movimento_financeiro_service import (
    MovimentoFinanceiroNaoEncontrado,
)
from app.services.movimento_financeiro_service import MovimentoFinanceiroService


router = APIRouter(
    prefix="/movimentos-financeiros",
    tags=["Movimentos Financeiros"],
)


def _get_service(db: Session) -> MovimentoFinanceiroService:
    """Instancia o service de movimento financeiro com o repository."""
    return MovimentoFinanceiroService(MovimentoFinanceiroRepository(db))


def _mapear_excecao(exc: Exception) -> NoReturn:
    """
    Converte exceções de domínio em HTTPException.

    Tratamento temporário na camada API até existir handler global.
    """
    if isinstance(exc, MovimentoFinanceiroNaoEncontrado):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    raise exc


@router.get("", response_model=list[MovimentoFinanceiroResponse])
def listar(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> list[MovimentoFinanceiroResponse]:
    """Lista movimentos financeiros ativos com paginação."""
    _ = usuario
    service = _get_service(db)
    return service.listar(skip=skip, limit=limit)


@router.get("/{movimento_id}", response_model=MovimentoFinanceiroResponse)
def buscar(
    movimento_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> MovimentoFinanceiroResponse:
    """Busca movimento financeiro ativo pelo identificador."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.buscar_por_id(movimento_id)
    except MovimentoFinanceiroNaoEncontrado as exc:
        _mapear_excecao(exc)


@router.post(
    "",
    response_model=MovimentoFinanceiroResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar(
    dados: MovimentoFinanceiroCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> MovimentoFinanceiroResponse:
    """Cadastra um novo movimento financeiro."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.criar(dados)
    except MovimentoFinanceiroNaoEncontrado as exc:
        _mapear_excecao(exc)


@router.put("/{movimento_id}", response_model=MovimentoFinanceiroResponse)
def atualizar(
    movimento_id: int,
    dados: MovimentoFinanceiroUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> MovimentoFinanceiroResponse:
    """Atualiza campos informados de um movimento financeiro ativo."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.atualizar(movimento_id, dados)
    except MovimentoFinanceiroNaoEncontrado as exc:
        _mapear_excecao(exc)


@router.delete("/{movimento_id}", response_model=MovimentoFinanceiroResponse)
def excluir(
    movimento_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> MovimentoFinanceiroResponse:
    """Exclusão lógica do movimento financeiro (ativo = False)."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.excluir(movimento_id)
    except MovimentoFinanceiroNaoEncontrado as exc:
        _mapear_excecao(exc)
