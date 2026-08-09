"""
Schemas Pydantic do cadastro de Inventários (EPIC 002).
"""

from datetime import date
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class InventarioCreate(BaseModel):
    """
    Payload de criação de inventário.

    status não é aceito aqui — novos inventários iniciam como "aberto".
    """

    data_inventario: date
    usuario_id: int
    observacao: str = Field(default="", max_length=500)


class InventarioUpdate(BaseModel):
    """
    Payload de atualização parcial de inventário.

    status não é aceito — conclusão ocorre apenas via concluir(...).
    """

    data_inventario: Optional[date] = None
    usuario_id: Optional[int] = None
    observacao: Optional[str] = Field(None, max_length=500)


class InventarioResponse(BaseModel):
    """Representação de inventário retornada pela API."""

    id: int
    data_inventario: date
    usuario_id: int
    observacao: str
    status: str
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True
