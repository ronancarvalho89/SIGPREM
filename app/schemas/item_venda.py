"""
Schemas Pydantic do cadastro de Itens de Venda (COMMIT 0029).
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ItemVendaBase(BaseModel):
    """Campos base do item de venda."""

    venda_id: UUID
    produto_id: int
    quantidade: Decimal
    valor_unitario: Decimal
    valor_total: Decimal


class ItemVendaCreate(ItemVendaBase):
    """Payload de criação de item de venda."""


class ItemVendaUpdate(BaseModel):
    """Payload de atualização parcial de item de venda."""

    venda_id: Optional[UUID] = None
    produto_id: Optional[int] = None
    quantidade: Optional[Decimal] = None
    valor_unitario: Optional[Decimal] = None
    valor_total: Optional[Decimal] = None


class ItemVendaResponse(ItemVendaBase):
    """Representação de item de venda retornada pela API."""

    id: int
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True
