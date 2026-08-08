"""
Schemas Pydantic do cadastro de Movimentos Financeiros (COMMIT 0024).
"""

from datetime import date
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from app.models.movimento_financeiro import TipoMovimentoFinanceiro


class MovimentoFinanceiroBase(BaseModel):
    """Campos base do movimento financeiro."""

    tipo: TipoMovimentoFinanceiro
    data_movimento: date
    valor: Decimal
    descricao: str = Field(..., max_length=200)
    observacao: str = Field(default="", max_length=500)


class MovimentoFinanceiroCreate(MovimentoFinanceiroBase):
    """Payload de criação de movimento financeiro."""


class MovimentoFinanceiroUpdate(BaseModel):
    """Payload de atualização parcial de movimento financeiro."""

    tipo: Optional[TipoMovimentoFinanceiro] = None
    data_movimento: Optional[date] = None
    valor: Optional[Decimal] = None
    descricao: Optional[str] = Field(None, max_length=200)
    observacao: Optional[str] = Field(None, max_length=500)


class MovimentoFinanceiroResponse(MovimentoFinanceiroBase):
    """Representação de movimento financeiro retornada pela API."""

    id: int
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True
