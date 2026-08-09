"""
Schemas Pydantic do módulo de Auditoria (EPIC 001).

AuditoriaCreate é de uso interno dos Services.
A API pública de Auditoria é somente consulta.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class AuditoriaCreate(BaseModel):
    """Payload de criação de registro de auditoria."""

    usuario_id: Optional[int] = Field(default=None, ge=1)
    modulo: str = Field(..., min_length=1, max_length=100)
    acao: str = Field(..., min_length=1, max_length=100)
    entidade: str = Field(..., min_length=1, max_length=100)
    entidade_id: int = Field(..., ge=0)
    descricao: str = Field(default="", max_length=500)
    data_hora: Optional[datetime] = None


class AuditoriaResponse(BaseModel):
    """Representação de registro de auditoria retornada pela API."""

    id: int
    usuario_id: Optional[int]
    modulo: str
    acao: str
    entidade: str
    entidade_id: int
    descricao: str
    data_hora: datetime
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True
