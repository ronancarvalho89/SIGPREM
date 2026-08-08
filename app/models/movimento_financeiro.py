"""
Model MovimentoFinanceiro — eventos financeiros do SIGPREM (COMMIT 0023).

Preparado para registrar movimentos originados de compra de concreto,
produção, venda e ajustes financeiros.
"""

from datetime import date
from decimal import Decimal
import enum

from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import Numeric
from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Entity


class TipoMovimentoFinanceiro(enum.Enum):
    """Classificação do movimento financeiro."""

    COMPRA_CONCRETO = "COMPRA_CONCRETO"
    PRODUCAO = "PRODUCAO"
    VENDA = "VENDA"
    AJUSTE = "AJUSTE"


class MovimentoFinanceiro(Entity):

    __tablename__ = "movimentos_financeiros"

    tipo: Mapped[TipoMovimentoFinanceiro] = mapped_column(
        Enum(TipoMovimentoFinanceiro),
        nullable=False
    )

    data_movimento: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    valor: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    descricao: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    observacao: Mapped[str] = mapped_column(
        String(500),
        default=""
    )
