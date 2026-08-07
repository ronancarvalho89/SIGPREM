from pydantic import BaseModel


class UsuarioResponse(BaseModel):

    id: int

    login: str

    ativo: bool

    class Config:

        from_attributes = True
