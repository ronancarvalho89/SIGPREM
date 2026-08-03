from decimal import Decimal
from datetime import date

from pydantic import BaseModel


class CompraConcretoCreate(BaseModel):

    fornecedor_id: int

    data_compra: date

    nota_fiscal: str = ""

    quantidade_comprada: Decimal

    quantidade_recebida: Decimal

    valor_total: Decimal

    observacao: str = ""