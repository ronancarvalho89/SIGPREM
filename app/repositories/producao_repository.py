"""
Repository de Produção — acesso a dados (COMMIT 0049).

Responsável exclusivamente por operações de persistência.
Não contém regras de negócio.
"""

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.producao import Producao


class ProducaoRepository:
    """Acesso ao banco de dados para a entidade Producao."""

    def __init__(self, db: Session) -> None:
        """Inicializa o repository com a sessão do banco."""
        self.db = db

    def criar(self, producao: Producao) -> Producao:
        """Persiste uma nova produção."""
        self.db.add(producao)
        self.db.commit()
        self.db.refresh(producao)
        return producao

    def listar(self, skip: int = 0, limit: int = 50) -> list[Producao]:
        """Lista produções ativas com paginação (id DESC)."""
        return (
            self.db.query(Producao)
            .filter(Producao.ativo.is_(True))
            .order_by(Producao.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def listar_ativas_por_periodo(
        self,
        data_inicial: date,
        data_final: date,
    ) -> list[Producao]:
        """Lista produções ativas no intervalo de datas (inclusivo)."""
        return (
            self.db.query(Producao)
            .filter(
                Producao.ativo.is_(True),
                Producao.data >= data_inicial,
                Producao.data <= data_final,
            )
            .order_by(Producao.data.desc())
            .all()
        )

    def buscar_por_id(self, producao_id: int) -> Optional[Producao]:
        """Busca produção ativa pelo identificador."""
        return (
            self.db.query(Producao)
            .filter(
                Producao.id == producao_id,
                Producao.ativo.is_(True),
            )
            .first()
        )

    def atualizar(self, producao: Producao) -> Producao:
        """Persiste alterações em uma produção existente."""
        self.db.commit()
        self.db.refresh(producao)
        return producao

    def inativar(self, producao: Producao) -> Producao:
        """
        Realiza exclusão lógica (soft delete).

        Nunca remove o registro fisicamente.
        """
        producao.ativo = False
        self.db.commit()
        self.db.refresh(producao)
        return producao
