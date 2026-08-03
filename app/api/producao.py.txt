from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.producao import ProducaoCreate

from app.services.producao_service import (
    ProducaoService
)

router = APIRouter(
    prefix="/producao",
    tags=["Produção"]
)


@router.post("")
def produzir(

    dados: ProducaoCreate,

    db: Session = Depends(get_db)

):

    service = ProducaoService(db)

    return service.criar(dados)