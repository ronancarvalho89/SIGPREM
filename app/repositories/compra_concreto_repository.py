"""
Repository de Compra de Concreto — acesso a dados (COMMIT 0006).

Responsável exclusivamente por operações de persistência.
Não contém regras de negócio.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.compra_concreto import CompraConcreto


class CompraConcretoRepository:
    """Acesso ao banco de dados para a entidade CompraConcreto."""

    def __init__(self, db: Session) -> None:
        """Inicializa o repository com a sessão do banco."""
        self.db = db

    def criar(self, compra: CompraConcreto) -> CompraConcreto:
        """Persiste uma nova compra de concreto."""
        self.db.add(compra)
        self.db.commit()
        self.db.refresh(compra)
        return compra

    def listar(self, skip: int = 0, limit: int = 50) -> list[CompraConcreto]:
        """Lista compras ativas com paginação (id DESC)."""
        return (
            self.db.query(CompraConcreto)
            .filter(CompraConcreto.ativo.is_(True))
            .order_by(CompraConcreto.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def buscar_por_id(self, compra_id: int) -> Optional[CompraConcreto]:
        """Busca compra ativa pelo identificador."""
        return (
            self.db.query(CompraConcreto)
            .filter(
                CompraConcreto.id == compra_id,
                CompraConcreto.ativo.is_(True),
            )
            .first()
        )

    def buscar_por_nota_fiscal(self, nota_fiscal: str) -> Optional[CompraConcreto]:
        """Busca compra ativa pela nota fiscal."""
        return (
            self.db.query(CompraConcreto)
            .filter(
                CompraConcreto.nota_fiscal == nota_fiscal,
                CompraConcreto.ativo.is_(True),
            )
            .first()
        )

    def atualizar(self, compra: CompraConcreto) -> CompraConcreto:
        """Persiste alterações em uma compra existente."""
        self.db.commit()
        self.db.refresh(compra)
        return compra

    def inativar(self, compra: CompraConcreto) -> CompraConcreto:
        """
        Realiza exclusão lógica (soft delete).

        Nunca remove o registro fisicamente.
        """
        compra.ativo = False
        self.db.commit()
        self.db.refresh(compra)
        return compra
