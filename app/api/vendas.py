"""
Router de Vendas — endpoints HTTP do cadastro (COMMIT 0048).

Mapeia temporariamente exceções de domínio para HTTPException.
No futuro existirá um middleware/handler global de exceções.
"""

from datetime import date
from typing import Any
from typing import NoReturn
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import status
from sqlalchemy.orm import Session

from app.core.security import get_current_usuario
from app.database.database import get_db
from app.models.usuario import Usuario
from app.repositories.venda_repository import VendaRepository
from app.schemas.venda import VendaCreate
from app.schemas.venda import VendaResponse
from app.schemas.venda import VendaUpdate
from app.services.venda_service import EstoqueInsuficiente
from app.services.venda_service import VendaDuplicada
from app.services.venda_service import VendaJaEfetivada
from app.services.venda_service import VendaNaoEncontrada
from app.services.venda_service import VendaService


router = APIRouter(
    prefix="/vendas",
    tags=["Vendas"],
)


def _get_service(db: Session) -> VendaService:
    """Instancia o service de venda com o repository."""
    return VendaService(VendaRepository(db))


def _mapear_excecao(exc: Exception) -> NoReturn:
    """
    Converte exceções de domínio em HTTPException.

    Tratamento temporário na camada API até existir handler global.
    """
    if isinstance(exc, VendaNaoEncontrada):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if isinstance(exc, VendaDuplicada):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if isinstance(exc, EstoqueInsuficiente):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if isinstance(exc, VendaJaEfetivada):
        # Mesmo padrão de InventarioJaConcluido: regra de negócio → 400.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    raise exc


@router.get("", response_model=list[VendaResponse])
def listar(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> list[VendaResponse]:
    """Lista vendas ativas com paginação (data_venda DESC)."""
    _ = usuario
    service = _get_service(db)
    return service.listar(skip=skip, limit=limit)


@router.get("/relatorio/periodo")
def obter_relatorio_periodo(
    data_inicial: date = Query(...),
    data_final: date = Query(...),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> dict[str, Any]:
    """Retorna o relatório gerencial de vendas no período informado."""
    _ = usuario

    if data_inicial > data_final:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="data_inicial não pode ser posterior a data_final.",
        )

    service = _get_service(db)
    return service.relatorio_periodo(data_inicial, data_final)


@router.get("/{venda_id}", response_model=VendaResponse)
def buscar(
    venda_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> VendaResponse:
    """Busca venda ativa pelo identificador."""
    _ = usuario
    service = _get_service(db)

    try:
        return service.buscar_por_id(venda_id)
    except (VendaNaoEncontrada, VendaDuplicada) as exc:
        _mapear_excecao(exc)


@router.post(
    "",
    response_model=VendaResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar(
    dados: VendaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> VendaResponse:
    """Cadastra venda completa (itens, estoque e financeiro)."""
    service = _get_service(db)

    try:
        return service.criar(dados, usuario_id=usuario.id)
    except (
        VendaNaoEncontrada,
        VendaDuplicada,
        EstoqueInsuficiente,
    ) as exc:
        _mapear_excecao(exc)


@router.put("/{venda_id}", response_model=VendaResponse)
def atualizar(
    venda_id: UUID,
    dados: VendaUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> VendaResponse:
    """Bloqueado para venda efetivada (Pacote 4.6.1)."""
    service = _get_service(db)

    try:
        return service.atualizar(
            venda_id,
            dados,
            usuario_id=usuario.id,
        )
    except (
        VendaNaoEncontrada,
        VendaDuplicada,
        EstoqueInsuficiente,
        VendaJaEfetivada,
    ) as exc:
        _mapear_excecao(exc)


@router.delete("/{venda_id}", response_model=VendaResponse)
def excluir(
    venda_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> VendaResponse:
    """Bloqueado para venda efetivada (sem estorno nesta etapa)."""
    service = _get_service(db)

    try:
        return service.excluir(venda_id, usuario_id=usuario.id)
    except (
        VendaNaoEncontrada,
        VendaDuplicada,
        EstoqueInsuficiente,
        VendaJaEfetivada,
    ) as exc:
        _mapear_excecao(exc)
