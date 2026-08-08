"""
Schemas Pydantic do cadastro de Movimentos de Estoque (COMMIT 0016).
"""

from datetime import date
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from app.models.movimento_estoque import TipoMovimentoEstoque


class MovimentoEstoqueCreate(BaseModel):
    """Payload de criação de movimento de estoque."""

    data: date
    produto_id: int
    quantidade: Decimal
    tipo: TipoMovimentoEstoque
    producao_id: Optional[int] = None
    observacao: str = Field(default="", max_length=500)


class MovimentoEstoqueUpdate(BaseModel):
    """Payload de atualização parcial de movimento de estoque."""

    data: Optional[date] = None
    produto_id: Optional[int] = None
    quantidade: Optional[Decimal] = None
    tipo: Optional[TipoMovimentoEstoque] = None
    producao_id: Optional[int] = None
    observacao: Optional[str] = Field(None, max_length=500)


class MovimentoEstoqueResponse(BaseModel):
    """Representação de movimento de estoque retornada pela API."""

    id: int
    data: date
    produto_id: int
    quantidade: Decimal
    tipo: TipoMovimentoEstoque
    producao_id: Optional[int]
    observacao: str
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True
