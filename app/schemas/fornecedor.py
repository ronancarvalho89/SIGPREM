"""
Schemas Pydantic do cadastro de Fornecedores (COMMIT 0004).
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class FornecedorCreate(BaseModel):
    """Payload de criação de fornecedor."""

    razao_social: str = Field(..., max_length=200)
    cpf_cnpj: str = Field(..., max_length=20)
    telefone: str = Field(default="", max_length=30)
    email: str = Field(default="", max_length=120)
    observacao: str = Field(default="", max_length=500)


class FornecedorUpdate(BaseModel):
    """Payload de atualização parcial de fornecedor."""

    razao_social: Optional[str] = Field(None, max_length=200)
    cpf_cnpj: Optional[str] = Field(None, max_length=20)
    telefone: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = Field(None, max_length=120)
    observacao: Optional[str] = Field(None, max_length=500)


class FornecedorResponse(BaseModel):
    """Representação de fornecedor retornada pela API."""

    id: int
    razao_social: str
    cpf_cnpj: str
    telefone: str
    email: str
    observacao: str
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True
