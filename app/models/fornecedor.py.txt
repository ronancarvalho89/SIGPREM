from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Entity


class Fornecedor(Entity):

    __tablename__ = "fornecedores"

    razao_social: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    cpf_cnpj: Mapped[str] = mapped_column(
        String(20),
        unique=True
    )

    telefone: Mapped[str] = mapped_column(
        String(30),
        default=""
    )

    email: Mapped[str] = mapped_column(
        String(120),
        default=""
    )

    observacao: Mapped[str] = mapped_column(
        String(500),
        default=""
    )