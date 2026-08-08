"""
Repository de Venda — acesso a dados (COMMIT 0047).

Responsável exclusivamente por operações de persistência.
Não contém regras de negócio.
"""

from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.venda import Venda


class VendaRepository:
    """Acesso ao banco de dados para a entidade Venda."""

    def __init__(self, db: Session) -> None:
        """Inicializa o repository com a sessão do banco."""
        self.db = db

    def criar(self, venda: Venda) -> Venda:
        """Persiste uma nova venda."""
        self.db.add(venda)
        self.db.commit()
        self.db.refresh(venda)
        return venda

    def listar(self, skip: int = 0, limit: int = 50) -> list[Venda]:
        """Lista vendas ativas com paginação (data_venda DESC)."""
        return (
            self.db.query(Venda)
            .filter(Venda.ativo.is_(True))
            .order_by(Venda.data_venda.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def listar_ativas_por_periodo(
        self,
        data_inicial: date,
        data_final: date,
    ) -> list[Venda]:
        """Lista vendas ativas no intervalo de datas (inclusivo)."""
        return (
            self.db.query(Venda)
            .filter(
                Venda.ativo.is_(True),
                Venda.data_venda >= data_inicial,
                Venda.data_venda <= data_final,
            )
            .order_by(Venda.data_venda.desc())
            .all()
        )

    def buscar_por_id(self, venda_id: UUID) -> Optional[Venda]:
        """Busca venda ativa pelo identificador."""
        return (
            self.db.query(Venda)
            .filter(
                Venda.id == venda_id,
                Venda.ativo.is_(True),
            )
            .first()
        )

    def buscar_por_numero(self, numero: str) -> Optional[Venda]:
        """Busca venda ativa pelo número."""
        return (
            self.db.query(Venda)
            .filter(
                Venda.numero == numero,
                Venda.ativo.is_(True),
            )
            .first()
        )

    def atualizar(self, venda: Venda) -> Venda:
        """Persiste alterações em uma venda existente."""
        self.db.commit()
        self.db.refresh(venda)
        return venda

    def inativar(self, venda: Venda) -> Venda:
        """
        Realiza exclusão lógica (soft delete).

        Nunca remove o registro fisicamente.
        """
        venda.ativo = False
        self.db.commit()
        self.db.refresh(venda)
        return venda
