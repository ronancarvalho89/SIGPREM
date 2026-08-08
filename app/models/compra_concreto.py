"""
Model CompraConcreto — compras de concreto do SIGPREM (COMMIT 0013).

Herda de Entity (Base do projeto) para manter id, ativo, criado_em
e atualizado_em no mesmo padrão dos demais models.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Entity


class CompraConcreto(Entity):

    __tablename__ = "compras_concreto"

    fornecedor_id: Mapped[int] = mapped_column(
        ForeignKey("fornecedores.id"),
        nullable=False
    )

    data_compra: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    nota_fiscal: Mapped[str] = mapped_column(
        String(30),
        default=""
    )

    quantidade_comprada: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False
    )

    quantidade_recebida: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False
    )

    saldo: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False
    )

    valor_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    observacao: Mapped[str] = mapped_column(
        String(500),
        default=""
    )

    fornecedor = relationship("Fornecedor")
