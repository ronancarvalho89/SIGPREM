from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.repositories.compra_concreto_repository import CompraConcretoRepository

from app.services.compra_concreto_service import CompraConcretoService

from app.schemas.compra_concreto import CompraConcretoCreate

router = APIRouter(
    prefix="/compras-concreto",
    tags=["Compras de Concreto"]
)


@router.post("")
def criar(
    dados: CompraConcretoCreate,
    db: Session = Depends(get_db)
):

    service = CompraConcretoService(
        CompraConcretoRepository(db)
    )

    return service.criar(dados)


@router.get("")
def listar(
    db: Session = Depends(get_db)
):

    service = CompraConcretoService(
        CompraConcretoRepository(db)
    )

    return service.listar()