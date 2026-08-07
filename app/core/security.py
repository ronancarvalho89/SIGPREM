from datetime import datetime
from datetime import timedelta
from datetime import timezone

from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import OAuth2PasswordBearer
import bcrypt
from jose import JWTError
from jose import jwt
from sqlalchemy.orm import Session

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.config import SECRET_KEY
from app.database.database import get_db
from app.models.usuario import Usuario


ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def hash_password(senha: str) -> str:

    return bcrypt.hashpw(
        senha.encode(),
        bcrypt.gensalt()
    ).decode()


def verify_password(senha: str, senha_hash: str) -> bool:

    return bcrypt.checkpw(
        senha.encode(),
        senha_hash.encode()
    )


def create_access_token(data: dict) -> str:

    if not SECRET_KEY:

        raise RuntimeError("SECRET_KEY não configurada.")

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = data.copy()

    payload.update({"exp": expire})

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def decode_access_token(token: str) -> dict:

    if not SECRET_KEY:

        raise RuntimeError("SECRET_KEY não configurada.")

    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
    )


def get_current_usuario(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Usuario:

    from app.repositories.usuario_repository import UsuarioRepository
    from app.services.auth_service import AuthService
    from app.services.auth_service import TokenInvalido

    auth_service = AuthService(
        UsuarioRepository(db)
    )

    try:

        return auth_service.obter_usuario_por_token(token)

    except TokenInvalido:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except JWTError:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
