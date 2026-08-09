"""
Model ItemInventario — itens de um inventário de estoque (COMMIT 0064).
"""

from decimal import Decimal

from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Entity


class ItemInventario(Entity):

    __tablename__ = "itens_inventario"

    inventario_id: Mapped[int] = mapped_column(
        ForeignKey("inventarios.id"),
        nullable=False
    )

    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"),
        nullable=False
    )

    quantidade_sistema: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    quantidade_fisica: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    diferenca: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    observacao: Mapped[str] = mapped_column(
        String(500),
        default=""
    )

    inventario = relationship("Inventario")

    produto = relationship("Produto")
