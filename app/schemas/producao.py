from decimal import Decimal
from datetime import date

from pydantic import BaseModel


class ProducaoCreate(BaseModel):

    data: date

    funcionario_id: int

    produto_id: int

    compra_concreto_id: int

    quantidade_produzida: Decimal

    observacao: str = ""