"""
Schemas Pydantic do cadastro de Vendas (COMMIT 0011).
"""

from datetime import date
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field


class VendaCreate(BaseModel):
    """Payload de criação de venda."""

    cliente_id: int
    data_venda: date
    numero: str = Field(..., max_length=30)
    valor_total: Decimal = Decimal("0")
    observacoes: str = Field(default="", max_length=500)
    status: str = Field(default="ABERTA", max_length=30)


class VendaUpdate(BaseModel):
    """Payload de atualização parcial de venda."""

    cliente_id: Optional[int] = None
    data_venda: Optional[date] = None
    numero: Optional[str] = Field(None, max_length=30)
    valor_total: Optional[Decimal] = None
    observacoes: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, max_length=30)


class VendaResponse(BaseModel):
    """Representação de venda retornada pela API."""

    id: UUID
    cliente_id: int
    data_venda: date
    numero: str
    valor_total: Decimal
    observacoes: str
    status: str
    ativo: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
