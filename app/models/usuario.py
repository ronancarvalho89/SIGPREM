from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Entity


class Usuario(Entity):

    __tablename__ = "usuarios"

    login: Mapped[str] = mapped_column(
        String(80),
        unique=True,
        nullable=False
    )

    senha_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
