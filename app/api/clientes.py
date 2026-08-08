"""
Router de Clientes — endpoints HTTP do cadastro (COMMIT 0008).

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
from app.repositories.cliente_repository import ClienteRepository
from app.schemas.cliente import ClienteCreate
from app.schemas.cliente import ClienteResponse
from app.schemas.cliente import ClienteUpdate
from app.services.cliente_service import ClienteDuplicado
from app.services.cliente_service import ClienteNaoEncontrado
from app.services.cliente_service import ClienteService


router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"],
)


def _get_service(db: Session) -> ClienteService:
    """Instancia o service de cliente com o repository."""
    return ClienteService(ClienteRepository(db))


def _mapear_excecao(exc: Exception) -> NoReturn:
    """
    Converte exceções de domínio em HTTPException.

    Tratamento temporário na camada API até existir handler global.
    """
    if isinstance(exc, ClienteNaoEncontrado):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(exc, ClienteDuplicado):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    raise exc


@router.get("", response_model=list[ClienteResponse])
def listar(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> list[ClienteResponse]:
    """Lista clientes ativos com paginação (razao_social ASC)."""
    _ = usuario
    service = _get_service(db)
    return service.listar(skip=skip, limit=limit)


@router.get("/{cliente_id}", response_model=ClienteResponse)
def buscar(
    cliente_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ClienteResponse:
    """Busca cliente ativo pelo identificador."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.buscar_por_id(cliente_id)
    except (ClienteNaoEncontrado, ClienteDuplicado) as exc:
        _mapear_excecao(exc)


@router.post(
    "",
    response_model=ClienteResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar(
    dados: ClienteCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ClienteResponse:
    """Cadastra um novo cliente."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.criar(dados)
    except (ClienteNaoEncontrado, ClienteDuplicado) as exc:
        _mapear_excecao(exc)


@router.put("/{cliente_id}", response_model=ClienteResponse)
def atualizar(
    cliente_id: int,
    dados: ClienteUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ClienteResponse:
    """Atualiza campos informados de um cliente ativo."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.atualizar(cliente_id, dados)
    except (ClienteNaoEncontrado, ClienteDuplicado) as exc:
        _mapear_excecao(exc)


@router.delete("/{cliente_id}", response_model=ClienteResponse)
def excluir(
    cliente_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ClienteResponse:
    """Exclusão lógica do cliente (ativo = False)."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.excluir(cliente_id)
    except (ClienteNaoEncontrado, ClienteDuplicado) as exc:
        _mapear_excecao(exc)
