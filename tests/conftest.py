"""
Fixtures compartilhadas para testes do backend SIGPREM.

Mantém infraestrutura reutilizável entre módulos.
Fixtures específicas de um domínio devem ficar no respectivo
arquivo de teste.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.models.base import Base
from app.models.usuario import Usuario

# Models registrados no metadata para create_all (módulos com testes).
from app.models.auditoria import Auditoria  # noqa: F401
from app.models.compra_concreto import CompraConcreto  # noqa: F401
from app.models.fornecedor import Fornecedor  # noqa: F401
from app.models.funcionario import Funcionario  # noqa: F401
from app.models.inventario import Inventario  # noqa: F401
from app.models.item_inventario import ItemInventario  # noqa: F401
from app.models.movimento_estoque import MovimentoEstoque  # noqa: F401
from app.models.produto import Produto  # noqa: F401
from app.models.producao import Producao  # noqa: F401


@pytest.fixture()
def db_session() -> Session:
    """Sessão SQLite em memória com as tabelas registradas no metadata."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
    )
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def usuario(db_session: Session) -> Usuario:
    """Usuário ativo reutilizável em testes que dependem de autenticação/FK."""
    user = Usuario(
        login="tester",
        senha_hash=hash_password("senha123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
