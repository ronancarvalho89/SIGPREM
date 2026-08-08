"""
Router de Itens de Venda — endpoints HTTP (COMMIT 0030).

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
from app.repositories.item_venda_repository import ItemVendaRepository
from app.schemas.item_venda import ItemVendaCreate
from app.schemas.item_venda import ItemVendaResponse
from app.schemas.item_venda import ItemVendaUpdate
from app.services.item_venda_service import ItemVendaNaoEncontrado
from app.services.item_venda_service import ItemVendaService


router = APIRouter(
    prefix="/itens-venda",
    tags=["Itens de Venda"],
)


def _get_service(db: Session) -> ItemVendaService:
    """Instancia o service de item de venda com o repository."""
    return ItemVendaService(ItemVendaRepository(db))


def _mapear_excecao(exc: Exception) -> NoReturn:
    """
    Converte exceções de domínio em HTTPException.

    Tratamento temporário na camada API até existir handler global.
    """
    if isinstance(exc, ItemVendaNaoEncontrado):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    raise exc


@router.get("", response_model=list[ItemVendaResponse])
def listar(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> list[ItemVendaResponse]:
    """Lista itens ativos com paginação (id DESC)."""
    _ = usuario
    service = _get_service(db)
    return service.listar(skip=skip, limit=limit)


@router.get("/{item_id}", response_model=ItemVendaResponse)
def buscar(
    item_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ItemVendaResponse:
    """Busca item ativo pelo identificador."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.buscar_por_id(item_id)
    except ItemVendaNaoEncontrado as exc:
        _mapear_excecao(exc)


@router.post(
    "",
    response_model=ItemVendaResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar(
    dados: ItemVendaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ItemVendaResponse:
    """Cadastra um novo item de venda."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.criar(dados)
    except ItemVendaNaoEncontrado as exc:
        _mapear_excecao(exc)


@router.put("/{item_id}", response_model=ItemVendaResponse)
def atualizar(
    item_id: int,
    dados: ItemVendaUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ItemVendaResponse:
    """Atualiza campos informados de um item ativo."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.atualizar(item_id, dados)
    except ItemVendaNaoEncontrado as exc:
        _mapear_excecao(exc)


@router.delete("/{item_id}", response_model=ItemVendaResponse)
def excluir(
    item_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ItemVendaResponse:
    """Exclusão lógica do item (ativo = False)."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.excluir(item_id)
    except ItemVendaNaoEncontrado as exc:
        _mapear_excecao(exc)
