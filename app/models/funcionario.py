from datetime import date

from sqlalchemy import Date
from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Entity


class Funcionario(Entity):

    __tablename__ = "funcionarios"

    nome: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    cpf: Mapped[str] = mapped_column(
        String(14),
        unique=True
    )

    telefone: Mapped[str] = mapped_column(
        String(30),
        default=""
    )

    data_admissao: Mapped[date] = mapped_column(
        Date
    )