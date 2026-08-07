from app.core.security import hash_password
from app.database.database import SessionLocal
from app.database.database import engine
from app.models.base import Base
from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository


ADMIN_LOGIN = "admin"
ADMIN_SENHA = "admin123"


def executar_seed():

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:

        repository = UsuarioRepository(db)

        if repository.buscar_por_login(ADMIN_LOGIN) is None:

            admin = Usuario(
                login=ADMIN_LOGIN,
                senha_hash=hash_password(ADMIN_SENHA)
            )

            repository.criar(admin)

    finally:

        db.close()
