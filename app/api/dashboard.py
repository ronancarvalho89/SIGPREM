"""
Router de Dashboard — indicadores consolidados (COMMIT 0044).
"""

from typing import Any

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_usuario
from app.database.database import get_db
from app.models.usuario import Usuario
from app.repositories.dashboard_repository import DashboardRepository
from app.services.dashboard_service import DashboardService


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


def _get_service(db: Session) -> DashboardService:
    """Instancia o DashboardService com o repository."""
    return DashboardService(DashboardRepository(db))


@router.get("")
def obter_dashboard(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> dict[str, Any]:
    """Retorna o dashboard consolidado do sistema."""
    _ = usuario
    service = _get_service(db)
    return service.dashboard()
