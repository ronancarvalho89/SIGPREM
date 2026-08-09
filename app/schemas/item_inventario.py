"""
Schemas Pydantic do cadastro de Itens de Inventário (COMMIT 0066).
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class ItemInventarioBase(BaseModel):
    """Campos base do item de inventário."""

    inventario_id: int
    produto_id: int
    quantidade_sistema: Decimal
    quantidade_fisica: Decimal
    diferenca: Decimal
    observacao: str = Field(default="", max_length=500)


class ItemInventarioCreate(ItemInventarioBase):
    """Payload de criação de item de inventário."""


class ItemInventarioUpdate(BaseModel):
    """Payload de atualização parcial de item de inventário."""

    inventario_id: Optional[int] = None
    produto_id: Optional[int] = None
    quantidade_sistema: Optional[Decimal] = None
    quantidade_fisica: Optional[Decimal] = None
    diferenca: Optional[Decimal] = None
    observacao: Optional[str] = Field(None, max_length=500)


class ItemInventarioResponse(ItemInventarioBase):
    """Representação de item de inventário retornada pela API."""

    id: int
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True
