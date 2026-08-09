"""
Repository de Auditoria — acesso a dados (EPIC 001).

Responsável exclusivamente por operações de persistência.
Não contém regras de negócio.
Não remove registros fisicamente — apenas soft delete via inativar.
"""

from datetime import date
from datetime import datetime
from datetime import time
from typing import Optional

from sqlalchemy.orm import Session

from app.models.auditoria import Auditoria


class AuditoriaRepository:
    """Acesso ao banco de dados para a entidade Auditoria."""

    def __init__(self, db: Session) -> None:
        """Inicializa o repository com a sessão do banco."""
        self.db = db

    def criar(self, auditoria: Auditoria) -> Auditoria:
        """Persiste um novo registro de auditoria."""
        self.db.add(auditoria)
        self.db.commit()
        self.db.refresh(auditoria)
        return auditoria

    def listar(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Auditoria]:
        """Lista registros ativos com paginação (data_hora DESC)."""
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
        """Lista registros ativos com filtros opcionais e paginação."""
        query = self.db.query(Auditoria).filter(Auditoria.ativo.is_(True))

        if data_inicial is not None:
            inicio = datetime.combine(data_inicial, time.min)
            query = query.filter(Auditoria.data_hora >= inicio)

        if data_final is not None:
            fim = datetime.combine(data_final, time.max)
            query = query.filter(Auditoria.data_hora <= fim)

        if usuario_id is not None:
            query = query.filter(Auditoria.usuario_id == usuario_id)

        if modulo is not None:
            query = query.filter(Auditoria.modulo == modulo)

        if acao is not None:
            query = query.filter(Auditoria.acao == acao)

        if entidade is not None:
            query = query.filter(Auditoria.entidade == entidade)

        if entidade_id is not None:
            query = query.filter(Auditoria.entidade_id == entidade_id)

        return (
            query.order_by(Auditoria.data_hora.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def buscar_por_id(self, auditoria_id: int) -> Optional[Auditoria]:
        """Busca registro ativo pelo identificador."""
        return (
            self.db.query(Auditoria)
            .filter(
                Auditoria.id == auditoria_id,
                Auditoria.ativo.is_(True),
            )
            .first()
        )

    def inativar(self, auditoria: Auditoria) -> Auditoria:
        """
        Realiza exclusão lógica (soft delete).

        Nunca remove o registro fisicamente.
        """
        auditoria.ativo = False
        self.db.commit()
        self.db.refresh(auditoria)
        return auditoria
