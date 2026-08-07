"""
Schemas Pydantic do cadastro de Compras de Concreto (COMMIT 0006).
"""

from datetime import date
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class CompraConcretoCreate(BaseModel):
    """Payload de criação de compra de concreto."""

    fornecedor_id: int
    data_compra: date
    nota_fiscal: str = Field(default="", max_length=30)
    quantidade_comprada: Decimal
    quantidade_recebida: Decimal
    valor_total: Decimal
    observacao: str = Field(default="", max_length=500)


class CompraConcretoUpdate(BaseModel):
    """Payload de atualização parcial de compra de concreto."""

    fornecedor_id: Optional[int] = None
    data_compra: Optional[date] = None
    nota_fiscal: Optional[str] = Field(None, max_length=30)
    quantidade_comprada: Optional[Decimal] = None
    quantidade_recebida: Optional[Decimal] = None
    valor_total: Optional[Decimal] = None
    observacao: Optional[str] = Field(None, max_length=500)


class CompraConcretoResponse(BaseModel):
    """Representação de compra de concreto retornada pela API."""

    id: int
    fornecedor_id: int
    data_compra: date
    nota_fiscal: str
    quantidade_comprada: Decimal
    quantidade_recebida: Decimal
    saldo: Decimal
    valor_total: Decimal
    observacao: str
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True
