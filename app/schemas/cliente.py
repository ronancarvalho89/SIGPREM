from pydantic import BaseModel


class ClienteCreate(BaseModel):

    razao_social: str

    nome_fantasia: str

    cpf_cnpj: str

    telefone: str = ""

    whatsapp: str = ""

    email: str = ""

    observacao: str = ""


class ClienteResponse(ClienteCreate):

    id: int

    ativo: bool

    class Config:

        from_attributes = True