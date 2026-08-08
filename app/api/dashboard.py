"""
Router de Dashboard — indicadores agregados (COMMIT 0009).
"""

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


@router.get("")
def obter_dashboard(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> dict[str, int]:
    """Retorna os indicadores do dashboard."""
    _ = usuario
    service = DashboardService(DashboardRepository(db))
    return service.obter_indicadores()
