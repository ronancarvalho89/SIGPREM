"""
Schemas Pydantic do cadastro de Produção (COMMIT 0007).
"""

from datetime import date
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class ProducaoCreate(BaseModel):
    """Payload de criação de produção."""

    data: date
    funcionario_id: int
    produto_id: int
    compra_concreto_id: int
    quantidade_produzida: Decimal
    observacao: str = Field(default="", max_length=500)


class ProducaoUpdate(BaseModel):
    """Payload de atualização parcial de produção."""

    data: Optional[date] = None
    funcionario_id: Optional[int] = None
    observacao: Optional[str] = Field(None, max_length=500)


class ProducaoResponse(BaseModel):
    """Representação de produção retornada pela API."""

    id: int
    data: date
    funcionario_id: int
    produto_id: int
    compra_concreto_id: int
    quantidade_produzida: Decimal
    concreto_consumido: Decimal
    valor_producao: Decimal
    observacao: str
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True
