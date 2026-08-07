"""
Router de Compras de Concreto — endpoints HTTP do cadastro (COMMIT 0006).

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
from app.repositories.compra_concreto_repository import CompraConcretoRepository
from app.schemas.compra_concreto import CompraConcretoCreate
from app.schemas.compra_concreto import CompraConcretoResponse
from app.schemas.compra_concreto import CompraConcretoUpdate
from app.services.compra_concreto_service import CompraConcretoDuplicada
from app.services.compra_concreto_service import CompraConcretoNaoEncontrada
from app.services.compra_concreto_service import CompraConcretoService


router = APIRouter(
    prefix="/compras-concreto",
    tags=["Compras de Concreto"],
)


def _get_service(db: Session) -> CompraConcretoService:
    """Instancia o service de compra de concreto com o repository."""
    return CompraConcretoService(CompraConcretoRepository(db))


def _mapear_excecao(exc: Exception) -> NoReturn:
    """
    Converte exceções de domínio em HTTPException.

    Tratamento temporário na camada API até existir handler global.
    """
    if isinstance(exc, CompraConcretoNaoEncontrada):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(exc, CompraConcretoDuplicada):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    raise exc


@router.get("", response_model=list[CompraConcretoResponse])
def listar(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> list[CompraConcretoResponse]:
    """Lista compras ativas com paginação (id DESC)."""
    _ = usuario
    service = _get_service(db)
    return service.listar(skip=skip, limit=limit)


@router.get("/{compra_id}", response_model=CompraConcretoResponse)
def buscar(
    compra_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> CompraConcretoResponse:
    """Busca compra ativa pelo identificador."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.buscar_por_id(compra_id)
    except (CompraConcretoNaoEncontrada, CompraConcretoDuplicada) as exc:
        _mapear_excecao(exc)


@router.post(
    "",
    response_model=CompraConcretoResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar(
    dados: CompraConcretoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> CompraConcretoResponse:
    """Cadastra uma nova compra de concreto."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.criar(dados)
    except (CompraConcretoNaoEncontrada, CompraConcretoDuplicada) as exc:
        _mapear_excecao(exc)


@router.put("/{compra_id}", response_model=CompraConcretoResponse)
def atualizar(
    compra_id: int,
    dados: CompraConcretoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> CompraConcretoResponse:
    """Atualiza campos informados de uma compra ativa."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.atualizar(compra_id, dados)
    except (CompraConcretoNaoEncontrada, CompraConcretoDuplicada) as exc:
        _mapear_excecao(exc)


@router.delete("/{compra_id}", response_model=CompraConcretoResponse)
def excluir(
    compra_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> CompraConcretoResponse:
    """Exclusão lógica da compra (ativo = False)."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.excluir(compra_id)
    except (CompraConcretoNaoEncontrada, CompraConcretoDuplicada) as exc:
        _mapear_excecao(exc)
