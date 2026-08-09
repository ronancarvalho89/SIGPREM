"""
Model Inventario — inventário de estoque do SIGPREM (EPIC 002).

Representa o cabeçalho de um inventário físico de produtos.
status: "aberto" (padrão) | "concluido".
"""

from datetime import date

from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Entity


class Inventario(Entity):

    __tablename__ = "inventarios"

    data_inventario: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    observacao: Mapped[str] = mapped_column(
        String(500),
        default=""
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="aberto",
    )

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=False
    )
