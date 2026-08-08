"""
Schemas Pydantic de FuncionarioValorProduto (COMMIT 0020).
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class FuncionarioValorProdutoCreate(BaseModel):
    """Payload de criação de valor por funcionário/produto."""

    funcionario_id: int
    produto_id: int
    valor: Decimal


class FuncionarioValorProdutoUpdate(BaseModel):
    """Payload de atualização parcial de valor por funcionário/produto."""

    funcionario_id: Optional[int] = None
    produto_id: Optional[int] = None
    valor: Optional[Decimal] = None


class FuncionarioValorProdutoResponse(BaseModel):
    """Representação de valor por funcionário/produto retornada pela API."""

    id: int
    funcionario_id: int
    produto_id: int
    valor: Decimal
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True
