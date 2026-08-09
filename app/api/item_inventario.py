"""
Router de Itens de Inventário — endpoints HTTP (EPIC 002).

Mapeia temporariamente exceções de domínio para HTTPException.
No futuro existirá um middleware/handler global de exceções.
"""

from decimal import Decimal
from typing import NoReturn

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_usuario
from app.database.database import get_db
from app.models.usuario import Usuario
from app.repositories.inventario_repository import InventarioRepository
from app.repositories.item_inventario_repository import ItemInventarioRepository
from app.schemas.item_inventario import ItemInventarioCreate
from app.schemas.item_inventario import ItemInventarioResponse
from app.schemas.item_inventario import ItemInventarioUpdate
from app.services.inventario_service import InventarioJaConcluido
from app.services.inventario_service import InventarioNaoEncontrado
from app.services.inventario_service import InventarioService
from app.services.item_inventario_service import ItemInventarioNaoEncontrado
from app.services.item_inventario_service import ItemInventarioService


class ContagemFisicaRequest(BaseModel):
    """Payload para registro da contagem física."""

    quantidade_contada: Decimal


router = APIRouter(
    prefix="/inventario",
    tags=["Itens de Inventário"],
)


def _get_item_service(db: Session) -> ItemInventarioService:
    """Instancia o service de item de inventário com o repository."""
    return ItemInventarioService(ItemInventarioRepository(db))


def _get_inventario_service(db: Session) -> InventarioService:
    """Instancia o service de inventário com o repository."""
    return InventarioService(InventarioRepository(db))


def _mapear_excecao(exc: Exception) -> NoReturn:
    """
    Converte exceções de domínio em HTTPException.

    Tratamento temporário na camada API até existir handler global.
    """
    if isinstance(exc, ItemInventarioNaoEncontrado):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(exc, InventarioNaoEncontrado):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(exc, InventarioJaConcluido):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    raise exc


@router.get(
    "/{inventario_id}/itens",
    response_model=list[ItemInventarioResponse],
)
def listar_por_inventario(
    inventario_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> list[ItemInventarioResponse]:
    """Lista itens ativos vinculados ao inventário."""
    _ = usuario
    service = _get_item_service(db)
    return service.listar_por_inventario(inventario_id)


@router.post(
    "/{inventario_id}/itens",
    response_model=ItemInventarioResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar(
    inventario_id: int,
    dados: ItemInventarioCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ItemInventarioResponse:
    """Cadastra item via InventarioService.adicionar_item (saldo automático)."""
    _ = usuario
    service = _get_inventario_service(db)

    try:
        return service.adicionar_item(inventario_id, dados)
    except (
        InventarioNaoEncontrado,
        InventarioJaConcluido,
        ItemInventarioNaoEncontrado,
    ) as exc:
        _mapear_excecao(exc)


@router.get("/item/{item_id}", response_model=ItemInventarioResponse)
def buscar(
    item_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ItemInventarioResponse:
    """Busca item de inventário ativo pelo identificador."""
    _ = usuario
    service = _get_item_service(db)

    try:
        return service.buscar_por_id(item_id)
    except ItemInventarioNaoEncontrado as exc:
        _mapear_excecao(exc)


@router.put("/item/{item_id}", response_model=ItemInventarioResponse)
def atualizar(
    item_id: int,
    dados: ItemInventarioUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ItemInventarioResponse:
    """Atualiza campos informados de um item ativo."""
    _ = usuario
    service = _get_item_service(db)

    try:
        return service.atualizar(item_id, dados)
    except (
        ItemInventarioNaoEncontrado,
        InventarioNaoEncontrado,
        InventarioJaConcluido,
    ) as exc:
        _mapear_excecao(exc)


@router.delete("/item/{item_id}", response_model=ItemInventarioResponse)
def excluir(
    item_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ItemInventarioResponse:
    """Exclusão lógica do item (ativo = False)."""
    _ = usuario
    service = _get_item_service(db)

    try:
        return service.excluir(item_id)
    except (
        ItemInventarioNaoEncontrado,
        InventarioNaoEncontrado,
        InventarioJaConcluido,
    ) as exc:
        _mapear_excecao(exc)


@router.post(
    "/item/{item_id}/contagem",
    response_model=ItemInventarioResponse,
)
def registrar_contagem(
    item_id: int,
    dados: ContagemFisicaRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ItemInventarioResponse:
    """Registra a quantidade física e calcula a diferença do item."""
    _ = usuario
    service = _get_item_service(db)

    try:
        return service.registrar_quantidade_fisica(
            item_id,
            dados.quantidade_contada,
        )
    except (
        ItemInventarioNaoEncontrado,
        InventarioNaoEncontrado,
        InventarioJaConcluido,
    ) as exc:
        _mapear_excecao(exc)
