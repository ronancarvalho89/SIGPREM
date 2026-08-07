from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from app.core.security import get_current_usuario
from app.database.database import get_db
from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.auth import LoginRequest
from app.schemas.auth import TokenResponse
from app.schemas.usuario import UsuarioResponse
from app.services.auth_service import AuthService
from app.services.auth_service import CredenciaisInvalidas


router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"]
)


@router.post("/login", response_model=TokenResponse)
def login(
    dados: LoginRequest,
    db: Session = Depends(get_db)
):

    service = AuthService(
        UsuarioRepository(db)
    )

    try:

        return service.autenticar(dados)

    except CredenciaisInvalidas:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UsuarioResponse)
def me(
    usuario: Usuario = Depends(get_current_usuario)
):

    return usuario
