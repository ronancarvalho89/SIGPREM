"""
Router de Auditoria — endpoints HTTP de consulta (EPIC 001).

Somente consulta autenticada. Não expõe criação, alteração
nem exclusão (física ou lógica) de registros de auditoria.

Mapeia temporariamente exceções de domínio para HTTPException.
No futuro existirá um middleware/handler global de exceções.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import status
from sqlalchemy.orm import Session

from app.core.security import get_current_usuario
from app.database.database import get_db
from app.models.usuario import Usuario
from app.repositories.auditoria_repository import AuditoriaRepository
from app.schemas.auditoria import AuditoriaResponse
from app.services.auditoria_service import AuditoriaService


router = APIRouter(
    prefix="/auditoria",
    tags=["Auditoria"],
)


def _get_service(db: Session) -> AuditoriaService:
    """Instancia o service de auditoria com o repository."""
    return AuditoriaService(AuditoriaRepository(db))


@router.get("", response_model=list[AuditoriaResponse])
def listar(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    data_inicial: Optional[date] = Query(None),
    data_final: Optional[date] = Query(None),
    usuario_id: Optional[int] = Query(None, ge=1),
    modulo: Optional[str] = Query(None, max_length=100),
    acao: Optional[str] = Query(None, max_length=100),
    entidade: Optional[str] = Query(None, max_length=100),
    entidade_id: Optional[int] = Query(None, ge=1),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> list[AuditoriaResponse]:
    """Lista registros de auditoria ativos com filtros e paginação."""
    _ = usuario

    if (
        data_inicial is not None
        and data_final is not None
        and data_inicial > data_final
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="data_inicial não pode ser posterior a data_final.",
        )

    service = _get_service(db)
    return service.consultar(
        skip=skip,
        limit=limit,
        data_inicial=data_inicial,
        data_final=data_final,
        usuario_id=usuario_id,
        modulo=modulo,
        acao=acao,
        entidade=entidade,
        entidade_id=entidade_id,
    )
