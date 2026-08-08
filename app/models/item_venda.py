"""
Model ItemVenda — itens de produtos de uma venda (COMMIT 0028).
"""

from decimal import Decimal
import uuid

from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import Uuid

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Entity


class ItemVenda(Entity):

    __tablename__ = "itens_venda"

    venda_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("vendas.id"),
        nullable=False
    )

    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"),
        nullable=False
    )

    quantidade: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False
    )

    valor_unitario: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    valor_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    venda = relationship("Venda")

    produto = relationship("Produto")
