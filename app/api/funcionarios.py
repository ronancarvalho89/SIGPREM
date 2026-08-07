"""
Router de Funcionários — endpoints HTTP do cadastro (COMMIT 0005).

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
from app.repositories.funcionario_repository import FuncionarioRepository
from app.schemas.funcionario import FuncionarioCreate
from app.schemas.funcionario import FuncionarioResponse
from app.schemas.funcionario import FuncionarioUpdate
from app.services.funcionario_service import FuncionarioDuplicado
from app.services.funcionario_service import FuncionarioNaoEncontrado
from app.services.funcionario_service import FuncionarioService


router = APIRouter(
    prefix="/funcionarios",
    tags=["Funcionários"],
)


def _get_service(db: Session) -> FuncionarioService:
    """Instancia o service de funcionário com o repository."""
    return FuncionarioService(FuncionarioRepository(db))


def _mapear_excecao(exc: Exception) -> NoReturn:
    """
    Converte exceções de domínio em HTTPException.

    Tratamento temporário na camada API até existir handler global.
    """
    if isinstance(exc, FuncionarioNaoEncontrado):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(exc, FuncionarioDuplicado):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    raise exc


@router.get("", response_model=list[FuncionarioResponse])
def listar(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> list[FuncionarioResponse]:
    """Lista funcionários ativos com paginação (nome ASC)."""
    _ = usuario
    service = _get_service(db)
    return service.listar(skip=skip, limit=limit)


@router.get("/{funcionario_id}", response_model=FuncionarioResponse)
def buscar(
    funcionario_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> FuncionarioResponse:
    """Busca funcionário ativo pelo identificador."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.buscar_por_id(funcionario_id)
    except (FuncionarioNaoEncontrado, FuncionarioDuplicado) as exc:
        _mapear_excecao(exc)


@router.post(
    "",
    response_model=FuncionarioResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar(
    dados: FuncionarioCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> FuncionarioResponse:
    """Cadastra um novo funcionário."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.criar(dados)
    except (FuncionarioNaoEncontrado, FuncionarioDuplicado) as exc:
        _mapear_excecao(exc)


@router.put("/{funcionario_id}", response_model=FuncionarioResponse)
def atualizar(
    funcionario_id: int,
    dados: FuncionarioUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> FuncionarioResponse:
    """Atualiza campos informados de um funcionário ativo."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.atualizar(funcionario_id, dados)
    except (FuncionarioNaoEncontrado, FuncionarioDuplicado) as exc:
        _mapear_excecao(exc)


@router.delete("/{funcionario_id}", response_model=FuncionarioResponse)
def excluir(
    funcionario_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> FuncionarioResponse:
    """Exclusão lógica do funcionário (ativo = False)."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.excluir(funcionario_id)
    except (FuncionarioNaoEncontrado, FuncionarioDuplicado) as exc:
        _mapear_excecao(exc)
