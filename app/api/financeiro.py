"""
Router de Financeiro — fluxo de caixa (COMMIT 0037).
"""

from typing import Any

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_usuario
from app.database.database import get_db
from app.models.usuario import Usuario
from app.repositories.movimento_financeiro_repository import (
    MovimentoFinanceiroRepository,
)
from app.services.movimento_financeiro_service import MovimentoFinanceiroService


router = APIRouter(
    prefix="/financeiro",
    tags=["Financeiro"],
)


def _get_service(db: Session) -> MovimentoFinanceiroService:
    """Instancia o service de movimento financeiro com o repository."""
    return MovimentoFinanceiroService(MovimentoFinanceiroRepository(db))


@router.get("/fluxo-caixa")
def obter_fluxo_caixa(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> dict[str, Any]:
    """Retorna o resumo consolidado do fluxo de caixa."""
    _ = usuario
    service = _get_service(db)
    return service.fluxo_caixa()
