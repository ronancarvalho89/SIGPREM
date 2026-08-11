"""
Schemas Pydantic do cadastro de Vendas (EPIC 004).
"""

from datetime import date
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field


class ItemVendaCreateNested(BaseModel):
    """Item informado na criação da venda (sem venda_id)."""

    produto_id: int
    quantidade: Decimal
    valor_unitario: Decimal


class VendaCreate(BaseModel):
    """
    Payload de criação de venda completa.

    itens é obrigatório — o total efetivo é calculado pelo Service.
    valor_total no payload é ignorado quando há itens (compatibilidade).
    """

    cliente_id: int
    data_venda: date
    numero: str = Field(..., max_length=30)
    valor_total: Decimal = Decimal("0")
    observacoes: str = Field(default="", max_length=500)
    status: str = Field(default="ABERTA", max_length=30)
    itens: list[ItemVendaCreateNested] = Field(..., min_length=1)


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
