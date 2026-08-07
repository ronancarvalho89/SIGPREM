"""
Schemas Pydantic do cadastro de Produtos (COMMIT 0003).

TODO(SIGPREM-002): futura alteração do campo modelo para referencia.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from app.models.produto import CategoriaProduto
from app.models.produto import TipoProduto
from app.models.produto import UnidadeProduto


class ProdutoCreate(BaseModel):
    """Payload de criação de produto."""

    codigo: str = Field(..., max_length=30)
    descricao: str = Field(..., max_length=150)
    categoria: CategoriaProduto
    # TODO(SIGPREM-002): futura alteração de modelo para referencia
    modelo: str = Field(..., max_length=80)
    unidade: UnidadeProduto
    concreto_por_unidade: Decimal = Decimal("0")
    tipo_produto: TipoProduto = TipoProduto.PRE_MOLDADO


class ProdutoUpdate(BaseModel):
    """
    Payload de atualização parcial de produto.

    categoria e codigo são imutáveis após o cadastro.
    """

    descricao: Optional[str] = Field(None, max_length=150)
    # TODO(SIGPREM-002): futura alteração de modelo para referencia
    modelo: Optional[str] = Field(None, max_length=80)
    unidade: Optional[UnidadeProduto] = None
    concreto_por_unidade: Optional[Decimal] = None


class ProdutoResponse(BaseModel):
    """Representação de produto retornada pela API."""

    id: int
    codigo: str
    descricao: str
    categoria: CategoriaProduto
    # TODO(SIGPREM-002): futura alteração de modelo para referencia
    modelo: str
    unidade: UnidadeProduto
    concreto_por_unidade: Decimal
    tipo_produto: TipoProduto
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True
