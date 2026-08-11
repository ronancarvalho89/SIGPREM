"""
Testes do módulo de Auditoria (EPIC 001 — ETAPA 5).
"""

from datetime import date
from datetime import datetime
from datetime import timedelta

import pytest
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.main import app
from app.models.auditoria import Auditoria
from app.models.usuario import Usuario
from app.repositories.auditoria_repository import AuditoriaRepository
from app.schemas.auditoria import AuditoriaCreate
from app.services.auditoria_service import AuditoriaNaoEncontrada
from app.services.auditoria_service import AuditoriaService


@pytest.fixture()
def auditoria_service(db_session: Session) -> AuditoriaService:
    """AuditoriaService com repository na sessão de teste."""
    return AuditoriaService(AuditoriaRepository(db_session))


def _registrar(
    service: AuditoriaService,
    *,
    usuario_id: int | None = None,
    modulo: str = "venda",
    acao: str = "criar",
    entidade: str = "Venda",
    entidade_id: int = 1,
    descricao: str = "teste",
    data_hora: datetime | None = None,
) -> Auditoria:
    return service.registrar(
        AuditoriaCreate(
            usuario_id=usuario_id,
            modulo=modulo,
            acao=acao,
            entidade=entidade,
            entidade_id=entidade_id,
            descricao=descricao,
            data_hora=data_hora,
        )
    )


def test_criar_registro(
    auditoria_service: AuditoriaService,
    usuario: Usuario,
) -> None:
    registro = _registrar(
        auditoria_service,
        usuario_id=usuario.id,
        descricao="criação com usuário",
    )

    assert registro.id is not None
    assert registro.usuario_id == usuario.id
    assert registro.modulo == "venda"
    assert registro.ativo is True
    assert isinstance(registro.data_hora, datetime)


def test_registro_sem_usuario_id(
    auditoria_service: AuditoriaService,
) -> None:
    registro = _registrar(
        auditoria_service,
        usuario_id=None,
        modulo="financeiro",
        acao="criar",
        entidade="MovimentoFinanceiro",
        entidade_id=20,
    )

    assert registro.id is not None
    assert registro.usuario_id is None
    assert registro.modulo == "financeiro"


def test_buscar_por_id(
    auditoria_service: AuditoriaService,
    usuario: Usuario,
) -> None:
    criado = _registrar(auditoria_service, usuario_id=usuario.id)
    encontrado = auditoria_service.buscar_por_id(criado.id)

    assert encontrado.id == criado.id
    assert encontrado.descricao == criado.descricao


def test_registro_inexistente(
    auditoria_service: AuditoriaService,
) -> None:
    with pytest.raises(AuditoriaNaoEncontrada):
        auditoria_service.buscar_por_id(999_999)


def test_listagem(
    auditoria_service: AuditoriaService,
    usuario: Usuario,
) -> None:
    _registrar(auditoria_service, usuario_id=usuario.id, entidade_id=1)
    _registrar(auditoria_service, usuario_id=None, entidade_id=2)

    registros = auditoria_service.listar()

    assert len(registros) == 2


def test_paginacao(
    auditoria_service: AuditoriaService,
) -> None:
    for indice in range(5):
        _registrar(
            auditoria_service,
            entidade_id=indice + 1,
            descricao=f"item {indice}",
        )

    pagina = auditoria_service.listar(skip=2, limit=2)

    assert len(pagina) == 2


def test_filtro_por_periodo(
    auditoria_service: AuditoriaService,
) -> None:
    """Filtro por período com datas fixas (independente do relógio do sistema)."""
    data_inicial = date(2026, 8, 9)
    data_final = date(2026, 8, 10)
    _registrar(
        auditoria_service,
        entidade_id=1,
        data_hora=datetime(2026, 7, 31, 12, 0, 0),
        descricao="antigo",
    )
    recente = _registrar(
        auditoria_service,
        entidade_id=2,
        data_hora=datetime(2026, 8, 10, 12, 0, 0),
        descricao="recente",
    )

    resultado = auditoria_service.consultar(
        data_inicial=data_inicial,
        data_final=data_final,
    )

    assert len(resultado) == 1
    assert resultado[0].id == recente.id


def test_filtro_por_usuario(
    auditoria_service: AuditoriaService,
    usuario: Usuario,
    db_session: Session,
) -> None:
    outro = Usuario(
        login="outro_user",
        senha_hash=usuario.senha_hash,
    )
    db_session.add(outro)
    db_session.commit()
    db_session.refresh(outro)

    alvo = _registrar(auditoria_service, usuario_id=usuario.id, entidade_id=1)
    _registrar(auditoria_service, usuario_id=outro.id, entidade_id=2)

    resultado = auditoria_service.consultar(usuario_id=usuario.id)

    assert len(resultado) == 1
    assert resultado[0].id == alvo.id


def test_filtro_por_modulo(
    auditoria_service: AuditoriaService,
) -> None:
    alvo = _registrar(
        auditoria_service,
        modulo="inventario",
        entidade="Inventario",
        entidade_id=1,
    )
    _registrar(
        auditoria_service,
        modulo="venda",
        entidade="Venda",
        entidade_id=2,
    )

    resultado = auditoria_service.consultar(modulo="inventario")

    assert len(resultado) == 1
    assert resultado[0].id == alvo.id


def test_filtro_por_acao(
    auditoria_service: AuditoriaService,
) -> None:
    alvo = _registrar(
        auditoria_service,
        acao="concluir",
        entidade_id=1,
    )
    _registrar(
        auditoria_service,
        acao="criar",
        entidade_id=2,
    )

    resultado = auditoria_service.consultar(acao="concluir")

    assert len(resultado) == 1
    assert resultado[0].id == alvo.id


def test_filtro_por_entidade(
    auditoria_service: AuditoriaService,
) -> None:
    alvo = _registrar(
        auditoria_service,
        entidade="Producao",
        modulo="producao",
        entidade_id=1,
    )
    _registrar(
        auditoria_service,
        entidade="Venda",
        modulo="venda",
        entidade_id=2,
    )

    resultado = auditoria_service.consultar(entidade="Producao")

    assert len(resultado) == 1
    assert resultado[0].id == alvo.id


def test_filtro_por_entidade_id(
    auditoria_service: AuditoriaService,
) -> None:
    alvo = _registrar(auditoria_service, entidade_id=77)
    _registrar(auditoria_service, entidade_id=88)

    resultado = auditoria_service.consultar(entidade_id=77)

    assert len(resultado) == 1
    assert resultado[0].id == alvo.id


def test_soft_delete_nao_remove_fisicamente(
    auditoria_service: AuditoriaService,
    db_session: Session,
) -> None:
    registro = _registrar(auditoria_service, entidade_id=1)
    registro_id = registro.id

    AuditoriaRepository(db_session).inativar(registro)

    with pytest.raises(AuditoriaNaoEncontrada):
        auditoria_service.buscar_por_id(registro_id)

    assert auditoria_service.listar() == []

    fisico = (
        db_session.query(Auditoria)
        .filter(Auditoria.id == registro_id)
        .first()
    )
    assert fisico is not None
    assert fisico.ativo is False


def test_integracao_basica_auditoria_service(
    auditoria_service: AuditoriaService,
    usuario: Usuario,
) -> None:
    criado = auditoria_service.registrar(
        AuditoriaCreate(
            usuario_id=usuario.id,
            modulo="producao",
            acao="criar",
            entidade="Producao",
            entidade_id=15,
            descricao="integração básica",
        )
    )
    listados = auditoria_service.consultar(
        modulo="producao",
        acao="criar",
        entidade="Producao",
        entidade_id=15,
        usuario_id=usuario.id,
    )
    buscado = auditoria_service.buscar_por_id(criado.id)

    assert len(listados) == 1
    assert listados[0].id == criado.id
    assert buscado.descricao == "integração básica"


def test_api_auditoria_somente_consulta() -> None:
    metodos = set()
    for rota in app.routes:
        if not isinstance(rota, APIRoute):
            continue
        if rota.path != "/auditoria" and not rota.path.startswith(
            "/auditoria/"
        ):
            continue
        metodos.update(rota.methods or set())

    assert "GET" in metodos
    assert "DELETE" not in metodos
    assert "POST" not in metodos
    assert "PUT" not in metodos
    assert "PATCH" not in metodos


def test_filtro_texto_vazio_nao_restringe(
    auditoria_service: AuditoriaService,
) -> None:
    _registrar(auditoria_service, modulo="venda", entidade_id=1)
    _registrar(auditoria_service, modulo="producao", entidade_id=2)

    resultado = auditoria_service.consultar(modulo="   ")

    assert len(resultado) == 2
