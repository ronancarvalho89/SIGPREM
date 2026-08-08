"""
Model MovimentoEstoque — movimentos de estoque do SIGPREM (COMMIT 0015).

Representa entradas e saídas de produtos acabados.
Compatível com a futura geração de entrada em producao_service.
"""

from datetime import date
from decimal import Decimal
import enum
from typing import Optional

from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Entity


class TipoMovimentoEstoque(enum.Enum):
    """Tipos de movimento de estoque."""

    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"


class MovimentoEstoque(Entity):

    __tablename__ = "movimento_estoque"

    data: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"),
        nullable=False
    )

    quantidade: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    tipo: Mapped[TipoMovimentoEstoque] = mapped_column(
        Enum(TipoMovimentoEstoque),
        nullable=False
    )

    producao_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("producoes.id"),
        nullable=True
    )

    observacao: Mapped[str] = mapped_column(
        String(500),
        default=""
    )

    produto = relationship("Produto")

    producao = relationship("Producao")
