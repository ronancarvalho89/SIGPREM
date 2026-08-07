"""
Router de Fornecedores — endpoints HTTP do cadastro (COMMIT 0004).

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
from app.repositories.fornecedor_repository import FornecedorRepository
from app.schemas.fornecedor import FornecedorCreate
from app.schemas.fornecedor import FornecedorResponse
from app.schemas.fornecedor import FornecedorUpdate
from app.services.fornecedor_service import FornecedorDuplicado
from app.services.fornecedor_service import FornecedorNaoEncontrado
from app.services.fornecedor_service import FornecedorService


router = APIRouter(
    prefix="/fornecedores",
    tags=["Fornecedores"],
)


def _get_service(db: Session) -> FornecedorService:
    """Instancia o service de fornecedor com o repository."""
    return FornecedorService(FornecedorRepository(db))


def _mapear_excecao(exc: Exception) -> NoReturn:
    """
    Converte exceções de domínio em HTTPException.

    Tratamento temporário na camada API até existir handler global.
    """
    if isinstance(exc, FornecedorNaoEncontrado):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(exc, FornecedorDuplicado):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    raise exc


@router.get("", response_model=list[FornecedorResponse])
def listar(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> list[FornecedorResponse]:
    """Lista fornecedores ativos com paginação (razao_social ASC)."""
    _ = usuario
    service = _get_service(db)
    return service.listar(skip=skip, limit=limit)


@router.get("/{fornecedor_id}", response_model=FornecedorResponse)
def buscar(
    fornecedor_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> FornecedorResponse:
    """Busca fornecedor ativo pelo identificador."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.buscar_por_id(fornecedor_id)
    except (FornecedorNaoEncontrado, FornecedorDuplicado) as exc:
        _mapear_excecao(exc)


@router.post(
    "",
    response_model=FornecedorResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar(
    dados: FornecedorCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> FornecedorResponse:
    """Cadastra um novo fornecedor."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.criar(dados)
    except (FornecedorNaoEncontrado, FornecedorDuplicado) as exc:
        _mapear_excecao(exc)


@router.put("/{fornecedor_id}", response_model=FornecedorResponse)
def atualizar(
    fornecedor_id: int,
    dados: FornecedorUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> FornecedorResponse:
    """Atualiza campos informados de um fornecedor ativo."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.atualizar(fornecedor_id, dados)
    except (FornecedorNaoEncontrado, FornecedorDuplicado) as exc:
        _mapear_excecao(exc)


@router.delete("/{fornecedor_id}", response_model=FornecedorResponse)
def excluir(
    fornecedor_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> FornecedorResponse:
    """Exclusão lógica do fornecedor (ativo = False)."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.excluir(fornecedor_id)
    except (FornecedorNaoEncontrado, FornecedorDuplicado) as exc:
        _mapear_excecao(exc)
