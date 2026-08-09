"""
Router de Inventários — endpoints HTTP (COMMIT 0073).

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
from app.repositories.inventario_repository import InventarioRepository
from app.schemas.inventario import InventarioCreate
from app.schemas.inventario import InventarioResponse
from app.schemas.inventario import InventarioUpdate
from app.services.inventario_service import InventarioNaoEncontrado
from app.services.inventario_service import InventarioService


router = APIRouter(
    prefix="/inventarios",
    tags=["Inventários"],
)


def _get_service(db: Session) -> InventarioService:
    """Instancia o service de inventário com o repository."""
    return InventarioService(InventarioRepository(db))


def _mapear_excecao(exc: Exception) -> NoReturn:
    """
    Converte exceções de domínio em HTTPException.

    Tratamento temporário na camada API até existir handler global.
    """
    if isinstance(exc, InventarioNaoEncontrado):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    raise exc


@router.get("", response_model=list[InventarioResponse])
def listar(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> list[InventarioResponse]:
    """Lista inventários ativos com paginação (data_inventario DESC)."""
    _ = usuario
    service = _get_service(db)
    return service.listar(skip=skip, limit=limit)


@router.get("/{inventario_id}", response_model=InventarioResponse)
def buscar(
    inventario_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> InventarioResponse:
    """Busca inventário ativo pelo identificador."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.buscar_por_id(inventario_id)
    except InventarioNaoEncontrado as exc:
        _mapear_excecao(exc)


@router.post(
    "",
    response_model=InventarioResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar(
    dados: InventarioCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> InventarioResponse:
    """Cadastra um novo inventário."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.criar(dados)
    except InventarioNaoEncontrado as exc:
        _mapear_excecao(exc)


@router.put("/{inventario_id}", response_model=InventarioResponse)
def atualizar(
    inventario_id: int,
    dados: InventarioUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> InventarioResponse:
    """Atualiza campos informados de um inventário ativo."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.atualizar(inventario_id, dados)
    except InventarioNaoEncontrado as exc:
        _mapear_excecao(exc)


@router.delete("/{inventario_id}", response_model=InventarioResponse)
def excluir(
    inventario_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> InventarioResponse:
    """Exclusão lógica do inventário (ativo = False)."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.excluir(inventario_id)
    except InventarioNaoEncontrado as exc:
        _mapear_excecao(exc)
