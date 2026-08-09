"""
Model Auditoria — registro de auditoria do SIGPREM (EPIC 001).

Representa um evento auditável ocorrido no sistema.
usuario_id é opcional para operações sem usuário no contexto.
Exclusão física não é suportada — utilizar soft delete (ativo=False).
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Entity


class Auditoria(Entity):

    __tablename__ = "auditorias"

    usuario_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=True,
    )

    modulo: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    acao: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    entidade: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    entidade_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    descricao: Mapped[str] = mapped_column(
        String(500),
        default="",
    )

    data_hora: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
