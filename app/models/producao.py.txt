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


class Producao(Entity):

    __tablename__ = "producoes"

    data: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    funcionario_id: Mapped[int] = mapped_column(
        ForeignKey("funcionarios.id"),
        nullable=False
    )

    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"),
        nullable=False
    )

    compra_concreto_id: Mapped[int] = mapped_column(
        ForeignKey("compras_concreto.id"),
        nullable=False
    )

    quantidade_produzida: Mapped[Decimal] = mapped_column(
        Numeric(12,2),
        nullable=False
    )

    concreto_consumido: Mapped[Decimal] = mapped_column(
        Numeric(10,3),
        nullable=False
    )

    valor_producao: Mapped[Decimal] = mapped_column(
        Numeric(12,2),
        nullable=False
    )

    observacao: Mapped[str] = mapped_column(
        String(500),
        default=""
    )

    funcionario = relationship("Funcionario")

    produto = relationship("Produto")

    compra_concreto = relationship("CompraConcreto")