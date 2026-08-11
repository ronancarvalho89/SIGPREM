"""
Testes de Autenticação (EPIC 003 — ETAPA 7).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database.database import get_db
from app.main import app
from app.models.usuario import Usuario


@pytest.fixture()
def client_db(db_session: Session):
    """TestClient com DB de teste (sem bypass de autenticação)."""

    def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_login_valido(client_db: TestClient, usuario: Usuario) -> None:
    response = client_db.post(
        "/auth/login",
        json={"login": "tester", "senha": "senha123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]


def test_login_usuario_inexistente(client_db: TestClient) -> None:
    response = client_db.post(
        "/auth/login",
        json={"login": "naoexiste", "senha": "senha123"},
    )
    assert response.status_code == 401


def test_login_senha_incorreta(
    client_db: TestClient,
    usuario: Usuario,
) -> None:
    response = client_db.post(
        "/auth/login",
        json={"login": "tester", "senha": "errada"},
    )
    assert response.status_code == 401


def test_login_usuario_inativo(
    client_db: TestClient,
    db_session: Session,
) -> None:
    inativo = Usuario(
        login="inativo",
        senha_hash=hash_password("senha123"),
        ativo=False,
    )
    db_session.add(inativo)
    db_session.commit()

    response = client_db.post(
        "/auth/login",
        json={"login": "inativo", "senha": "senha123"},
    )
    assert response.status_code == 401


def test_me_autenticado(client_db: TestClient, usuario: Usuario) -> None:
    login = client_db.post(
        "/auth/login",
        json={"login": "tester", "senha": "senha123"},
    )
    token = login.json()["access_token"]

    me = client_db.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    body = me.json()
    assert body["login"] == "tester"
    assert body["id"] == usuario.id
    assert body["ativo"] is True


def test_me_sem_token(client_db: TestClient) -> None:
    assert client_db.get("/auth/me").status_code == 401


def test_me_token_invalido(client_db: TestClient) -> None:
    response = client_db.get(
        "/auth/me",
        headers={"Authorization": "Bearer token-invalido"},
    )
    assert response.status_code == 401


def test_endpoint_protegido_com_token_invalido(
    client_db: TestClient,
) -> None:
    response = client_db.get(
        "/dashboard",
        headers={"Authorization": "Bearer token-invalido"},
    )
    assert response.status_code == 401
