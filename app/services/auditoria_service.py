"""
Service de Auditoria — regras de negócio (EPIC 001).

Não lança HTTPException. Exceções de domínio são mapeadas na API.
No futuro existirá um middleware/handler global de exceções.
"""

from datetime import date
from datetime import datetime
from typing import Optional

from app.models.auditoria import Auditoria
from app.repositories.auditoria_repository import AuditoriaRepository
from app.schemas.auditoria import AuditoriaCreate


class AuditoriaNaoEncontrada(Exception):
    """Registro de auditoria ativo não encontrado."""


class AuditoriaService:
    """Regras de negócio do módulo de auditoria."""

    def __init__(self, repository: AuditoriaRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository

    def registrar(self, dados: AuditoriaCreate) -> Auditoria:
        """Registra um novo evento de auditoria."""
        campos = dados.model_dump(exclude_none=True)

        if "data_hora" not in campos:
            campos["data_hora"] = datetime.utcnow()

        auditoria = Auditoria(**campos)
        return self.repository.criar(auditoria)

    def listar(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Auditoria]:
        """Lista registros ativos com paginação."""
        return self.consultar(skip=skip, limit=limit)

    def consultar(
        self,
        skip: int = 0,
        limit: int = 50,
        data_inicial: Optional[date] = None,
        data_final: Optional[date] = None,
        usuario_id: Optional[int] = None,
        modulo: Optional[str] = None,
        acao: Optional[str] = None,
        entidade: Optional[str] = None,
        entidade_id: Optional[int] = None,
    ) -> list[Auditoria]:
        """Consulta registros ativos com filtros opcionais."""
        return self.repository.consultar(
            skip=skip,
            limit=limit,
            data_inicial=data_inicial,
            data_final=data_final,
            usuario_id=usuario_id,
            modulo=self._normalizar_filtro_texto(modulo),
            acao=self._normalizar_filtro_texto(acao),
            entidade=self._normalizar_filtro_texto(entidade),
            entidade_id=entidade_id,
        )

    def buscar_por_id(self, auditoria_id: int) -> Auditoria:
        """Retorna registro ativo por id ou levanta AuditoriaNaoEncontrada."""
        auditoria = self.repository.buscar_por_id(auditoria_id)

        if auditoria is None:
            raise AuditoriaNaoEncontrada(
                "Registro de auditoria não encontrado."
            )

        return auditoria

    def _normalizar_filtro_texto(
        self,
        valor: Optional[str],
    ) -> Optional[str]:
        """Normaliza filtro textual opcional (trim; vazio vira None)."""
        if valor is None:
            return None

        normalizado = valor.strip()
        if not normalizado:
            return None

        return normalizado
