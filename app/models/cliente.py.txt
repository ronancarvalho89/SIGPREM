from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Entity


class Cliente(Entity):

    __tablename__ = "clientes"

    razao_social: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    nome_fantasia: Mapped[str] = mapped_column(
        String(200),
        default=""
    )

    cpf_cnpj: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False
    )

    telefone: Mapped[str] = mapped_column(
        String(30),
        default=""
    )

    whatsapp: Mapped[str] = mapped_column(
        String(30),
        default=""
    )

    email: Mapped[str] = mapped_column(
        String(120),
        default=""
    )

    endereco: Mapped[str] = mapped_column(
        String(250),
        default=""
    )

    cidade: Mapped[str] = mapped_column(
        String(100),
        default=""
    )

    uf: Mapped[str] = mapped_column(
        String(2),
        default=""
    )

    cep: Mapped[str] = mapped_column(
        String(10),
        default=""
    )

    observacao: Mapped[str] = mapped_column(
        String(500),
        default=""
    )