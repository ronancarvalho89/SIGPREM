"""
Repository de Fornecedor — acesso a dados (COMMIT 0004).

Responsável exclusivamente por operações de persistência.
Não contém regras de negócio.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.fornecedor import Fornecedor


class FornecedorRepository:
    """Acesso ao banco de dados para a entidade Fornecedor."""

    def __init__(self, db: Session) -> None:
        """Inicializa o repository com a sessão do banco."""
        self.db = db

    def criar(self, fornecedor: Fornecedor) -> Fornecedor:
        """Persiste um novo fornecedor."""
        self.db.add(fornecedor)
        self.db.commit()
        self.db.refresh(fornecedor)
        return fornecedor

    def listar(self, skip: int = 0, limit: int = 50) -> list[Fornecedor]:
        """Lista fornecedores ativos com paginação (razao_social ASC)."""
        return (
            self.db.query(Fornecedor)
            .filter(Fornecedor.ativo.is_(True))
            .order_by(Fornecedor.razao_social.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def buscar_por_id(self, fornecedor_id: int) -> Optional[Fornecedor]:
        """Busca fornecedor ativo pelo identificador."""
        return (
            self.db.query(Fornecedor)
            .filter(
                Fornecedor.id == fornecedor_id,
                Fornecedor.ativo.is_(True),
            )
            .first()
        )

    def buscar_por_cpf_cnpj(self, cpf_cnpj: str) -> Optional[Fornecedor]:
        """Busca fornecedor ativo pelo CPF/CNPJ."""
        return (
            self.db.query(Fornecedor)
            .filter(
                Fornecedor.cpf_cnpj == cpf_cnpj,
                Fornecedor.ativo.is_(True),
            )
            .first()
        )

    def atualizar(self, fornecedor: Fornecedor) -> Fornecedor:
        """Persiste alterações em um fornecedor existente."""
        self.db.commit()
        self.db.refresh(fornecedor)
        return fornecedor

    def inativar(self, fornecedor: Fornecedor) -> Fornecedor:
        """
        Realiza exclusão lógica (soft delete).

        Nunca remove o registro fisicamente.
        """
        fornecedor.ativo = False
        self.db.commit()
        self.db.refresh(fornecedor)
        return fornecedor
