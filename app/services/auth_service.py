from jose import JWTError

from app.core.security import create_access_token
from app.core.security import decode_access_token
from app.core.security import verify_password
from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.auth import LoginRequest
from app.schemas.auth import TokenResponse


class CredenciaisInvalidas(Exception):
    pass


class TokenInvalido(Exception):
    pass


class AuthService:

    def __init__(self, repository: UsuarioRepository) -> None:

        self.repository = repository

    def autenticar(self, dados: LoginRequest) -> TokenResponse:

        usuario = self.repository.buscar_por_login(dados.login)

        if not usuario or not usuario.ativo:

            raise CredenciaisInvalidas()

        if not verify_password(dados.senha, usuario.senha_hash):

            raise CredenciaisInvalidas()

        token = create_access_token(
            {"sub": str(usuario.id)}
        )

        return TokenResponse(
            access_token=token
        )

    def obter_usuario_por_token(self, token: str) -> Usuario:

        try:

            payload = decode_access_token(token)

            usuario_id = payload.get("sub")

            if usuario_id is None:

                raise TokenInvalido()

            usuario = self.repository.buscar_por_id(int(usuario_id))

            if not usuario or not usuario.ativo:

                raise TokenInvalido()

            return usuario

        except JWTError:

            raise TokenInvalido()
