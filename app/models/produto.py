"""
Model Produto — cadastro de produtos do SIGPREM (COMMIT 0003).

Representa itens pré-moldados utilizados em produção, estoque,
pedidos e relatórios.

TODO(SIGPREM-001): futura migração Alembic para evolução do schema.
TODO(SIGPREM-002): futura alteração do campo modelo para referencia.
TODO(SIGPREM-004): índice parcial para Soft Delete (ativo = True).
"""

from decimal import Decimal
import enum

from sqlalchemy import Enum
from sqlalchemy import Index
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base import Entity


class CategoriaProduto(enum.Enum):
    """Categorias de produto disponíveis."""

    BLOQUETE = "BLOQUETE"
    MEIO_FIO = "MEIO_FIO"


class UnidadeProduto(enum.Enum):
    """Unidades de medida do produto."""

    M2 = "M2"
    UN = "UN"


class TipoProduto(enum.Enum):
    """
    Tipos de produto.

    Valor inicial: PRE_MOLDADO.
    Enum preparado para futuras expansões.
    """

    PRE_MOLDADO = "PRE_MOLDADO"


class Produto(Entity):
    """Entidade de produto do sistema."""

    __tablename__ = "produtos"

    __table_args__ = (
        Index("ix_produtos_codigo", "codigo", unique=True),
        # TODO(SIGPREM-004): índice parcial para Soft Delete
        # (ex.: UNIQUE(codigo) WHERE ativo = True via Alembic).
    )

    codigo: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    descricao: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
    )

    categoria: Mapped[CategoriaProduto] = mapped_column(
        Enum(CategoriaProduto),
        nullable=False,
    )

    # TODO(SIGPREM-002): futura alteração de modelo para referencia
    modelo: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    unidade: Mapped[UnidadeProduto] = mapped_column(
        Enum(UnidadeProduto),
        nullable=False,
    )

    concreto_por_unidade: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        default=0,
        nullable=False,
    )

    tipo_produto: Mapped[TipoProduto] = mapped_column(
        Enum(TipoProduto),
        default=TipoProduto.PRE_MOLDADO,
        nullable=False,
    )
