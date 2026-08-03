from decimal import Decimal

from sqlalchemy import Enum
from sqlalchemy import Numeric
from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Entity

import enum


class CategoriaProduto(enum.Enum):

    BLOQUETE = "BLOQUETE"

    MEIO_FIO = "MEIO_FIO"


class UnidadeProduto(enum.Enum):

    M2 = "M2"

    UN = "UN"


class Produto(Entity):

    __tablename__ = "produtos"

    descricao: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    categoria: Mapped[CategoriaProduto] = mapped_column(
        Enum(CategoriaProduto)
    )

    modelo: Mapped[str] = mapped_column(
        String(80)
    )

    unidade: Mapped[UnidadeProduto] = mapped_column(
        Enum(UnidadeProduto)
    )

    concreto_por_unidade: Mapped[Decimal] = mapped_column(
        Numeric(10,4),
        default=0
    )