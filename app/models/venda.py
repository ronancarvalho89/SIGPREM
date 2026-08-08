"""
Model Venda — entidade de vendas do SIGPREM (COMMIT 0010).
"""

from datetime import date
from datetime import datetime
from decimal import Decimal
import uuid

from sqlalchemy import Boolean
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Base


class Venda(Base):

    __tablename__ = "vendas"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id"),
        nullable=False
    )

    data_venda: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    numero: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    valor_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )

    observacoes: Mapped[str] = mapped_column(
        String(500),
        default=""
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="ABERTA"
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    cliente = relationship("Cliente")
