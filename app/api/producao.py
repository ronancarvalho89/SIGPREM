"""
Router de Produção — endpoints HTTP do cadastro (COMMIT 0007).

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
from app.repositories.producao_repository import ProducaoRepository
from app.schemas.producao import ProducaoCreate
from app.schemas.producao import ProducaoResponse
from app.schemas.producao import ProducaoUpdate
from app.services.producao_service import ProducaoDadosInvalidos
from app.services.producao_service import ProducaoNaoEncontrada
from app.services.producao_service import ProducaoService
from app.services.producao_service import SaldoConcretoInsuficiente


router = APIRouter(
    prefix="/producao",
    tags=["Produção"],
)


def _get_service(db: Session) -> ProducaoService:
    """Instancia o service de produção com o repository."""
    return ProducaoService(ProducaoRepository(db))


def _mapear_excecao(exc: Exception) -> NoReturn:
    """
    Converte exceções de domínio em HTTPException.

    Tratamento temporário na camada API até existir handler global.
    """
    if isinstance(exc, ProducaoNaoEncontrada):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(exc, SaldoConcretoInsuficiente):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if isinstance(exc, ProducaoDadosInvalidos):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    raise exc


@router.get("", response_model=list[ProducaoResponse])
def listar(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> list[ProducaoResponse]:
    """Lista produções ativas com paginação (id DESC)."""
    _ = usuario
    service = _get_service(db)
    return service.listar(skip=skip, limit=limit)


@router.get("/{producao_id}", response_model=ProducaoResponse)
def buscar(
    producao_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ProducaoResponse:
    """Busca produção ativa pelo identificador."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.buscar_por_id(producao_id)
    except (
        ProducaoNaoEncontrada,
        SaldoConcretoInsuficiente,
        ProducaoDadosInvalidos,
    ) as exc:
        _mapear_excecao(exc)


@router.post(
    "",
    response_model=ProducaoResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar(
    dados: ProducaoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ProducaoResponse:
    """Registra uma nova produção."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.criar(dados)
    except (
        ProducaoNaoEncontrada,
        SaldoConcretoInsuficiente,
        ProducaoDadosInvalidos,
    ) as exc:
        _mapear_excecao(exc)


@router.put("/{producao_id}", response_model=ProducaoResponse)
def atualizar(
    producao_id: int,
    dados: ProducaoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ProducaoResponse:
    """Atualiza campos permitidos de uma produção ativa."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.atualizar(producao_id, dados)
    except (
        ProducaoNaoEncontrada,
        SaldoConcretoInsuficiente,
        ProducaoDadosInvalidos,
    ) as exc:
        _mapear_excecao(exc)


@router.delete("/{producao_id}", response_model=ProducaoResponse)
def excluir(
    producao_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ProducaoResponse:
    """Exclusão lógica da produção (ativo = False)."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.excluir(producao_id)
    except (
        ProducaoNaoEncontrada,
        SaldoConcretoInsuficiente,
        ProducaoDadosInvalidos,
    ) as exc:
        _mapear_excecao(exc)
