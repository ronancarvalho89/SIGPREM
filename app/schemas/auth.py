from pydantic import BaseModel


class LoginRequest(BaseModel):

    login: str

    senha: str


class TokenResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"
