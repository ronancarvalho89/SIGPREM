"""
Model FuncionarioValorProduto — valor por funcionário/produto (COMMIT 0019).

Armazena o valor pago ao funcionário para cada produto produzido.
"""

from decimal import Decimal

from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import UniqueConstraint

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Entity


class FuncionarioValorProduto(Entity):

    __tablename__ = "funcionario_valor_produtos"

    __table_args__ = (
        UniqueConstraint(
            "funcionario_id",
            "produto_id",
            name="uq_funcionario_produto_valor",
        ),
    )

    funcionario_id: Mapped[int] = mapped_column(
        ForeignKey("funcionarios.id"),
        nullable=False
    )

    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"),
        nullable=False
    )

    valor: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    funcionario = relationship("Funcionario")

    produto = relationship("Produto")
