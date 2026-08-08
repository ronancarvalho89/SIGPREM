"""
Schemas Pydantic do cadastro de Clientes (COMMIT 0008).
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class ClienteCreate(BaseModel):
    """Payload de criação de cliente."""

    razao_social: str = Field(..., max_length=200)
    nome_fantasia: str = Field(default="", max_length=200)
    cpf_cnpj: str = Field(..., max_length=20)
    telefone: str = Field(default="", max_length=30)
    whatsapp: str = Field(default="", max_length=30)
    email: str = Field(default="", max_length=120)
    endereco: str = Field(default="", max_length=250)
    cidade: str = Field(default="", max_length=100)
    uf: str = Field(default="", max_length=2)
    cep: str = Field(default="", max_length=10)
    observacao: str = Field(default="", max_length=500)


class ClienteUpdate(BaseModel):
    """Payload de atualização parcial de cliente."""

    razao_social: Optional[str] = Field(None, max_length=200)
    nome_fantasia: Optional[str] = Field(None, max_length=200)
    cpf_cnpj: Optional[str] = Field(None, max_length=20)
    telefone: Optional[str] = Field(None, max_length=30)
    whatsapp: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = Field(None, max_length=120)
    endereco: Optional[str] = Field(None, max_length=250)
    cidade: Optional[str] = Field(None, max_length=100)
    uf: Optional[str] = Field(None, max_length=2)
    cep: Optional[str] = Field(None, max_length=10)
    observacao: Optional[str] = Field(None, max_length=500)


class ClienteResponse(BaseModel):
    """Representação de cliente retornada pela API."""

    id: int
    razao_social: str
    nome_fantasia: str
    cpf_cnpj: str
    telefone: str
    whatsapp: str
    email: str
    endereco: str
    cidade: str
    uf: str
    cep: str
    observacao: str
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True
