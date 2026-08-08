"""
Repository de Cliente — acesso a dados (COMMIT 0008).

Responsável exclusivamente por operações de persistência.
Não contém regras de negócio.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.cliente import Cliente


class ClienteRepository:
    """Acesso ao banco de dados para a entidade Cliente."""

    def __init__(self, db: Session) -> None:
        """Inicializa o repository com a sessão do banco."""
        self.db = db

    def criar(self, cliente: Cliente) -> Cliente:
        """Persiste um novo cliente."""
        self.db.add(cliente)
        self.db.commit()
        self.db.refresh(cliente)
        return cliente

    def listar(self, skip: int = 0, limit: int = 50) -> list[Cliente]:
        """Lista clientes ativos com paginação (razao_social ASC)."""
        return (
            self.db.query(Cliente)
            .filter(Cliente.ativo.is_(True))
            .order_by(Cliente.razao_social.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def buscar_por_id(self, cliente_id: int) -> Optional[Cliente]:
        """Busca cliente ativo pelo identificador."""
        return (
            self.db.query(Cliente)
            .filter(
                Cliente.id == cliente_id,
                Cliente.ativo.is_(True),
            )
            .first()
        )

    def buscar_por_cpf_cnpj(self, cpf_cnpj: str) -> Optional[Cliente]:
        """Busca cliente ativo pelo CPF/CNPJ."""
        return (
            self.db.query(Cliente)
            .filter(
                Cliente.cpf_cnpj == cpf_cnpj,
                Cliente.ativo.is_(True),
            )
            .first()
        )

    def atualizar(self, cliente: Cliente) -> Cliente:
        """Persiste alterações em um cliente existente."""
        self.db.commit()
        self.db.refresh(cliente)
        return cliente

    def inativar(self, cliente: Cliente) -> Cliente:
        """
        Realiza exclusão lógica (soft delete).

        Nunca remove o registro fisicamente.
        """
        cliente.ativo = False
        self.db.commit()
        self.db.refresh(cliente)
        return cliente
