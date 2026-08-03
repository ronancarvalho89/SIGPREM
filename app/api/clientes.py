from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.repositories.cliente_repository import ClienteRepository

from app.services.cliente_service import ClienteService

from app.schemas.cliente import ClienteCreate


router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)


@router.get("")
def listar(db: Session = Depends(get_db)):

    service = ClienteService(
        ClienteRepository(db)
    )

    return service.listar()


@router.post("")
def criar(
    dados: ClienteCreate,
    db: Session = Depends(get_db)
):

    service = ClienteService(
        ClienteRepository(db)
    )

    return service.criar(dados)