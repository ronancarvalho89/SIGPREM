"""
Schemas Pydantic do cadastro de Funcionários (COMMIT 0005).
"""

from datetime import date
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class FuncionarioCreate(BaseModel):
    """Payload de criação de funcionário."""

    nome: str = Field(..., max_length=150)
    cpf: str = Field(..., max_length=14)
    telefone: str = Field(default="", max_length=30)
    data_admissao: date


class FuncionarioUpdate(BaseModel):
    """Payload de atualização parcial de funcionário."""

    nome: Optional[str] = Field(None, max_length=150)
    cpf: Optional[str] = Field(None, max_length=14)
    telefone: Optional[str] = Field(None, max_length=30)
    data_admissao: Optional[date] = None


class FuncionarioResponse(BaseModel):
    """Representação de funcionário retornada pela API."""

    id: int
    nome: str
    cpf: str
    telefone: str
    data_admissao: date
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True
