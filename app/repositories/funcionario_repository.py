"""
Repository de Funcionário — acesso a dados (COMMIT 0005).

Responsável exclusivamente por operações de persistência.
Não contém regras de negócio.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.funcionario import Funcionario


class FuncionarioRepository:
    """Acesso ao banco de dados para a entidade Funcionario."""

    def __init__(self, db: Session) -> None:
        """Inicializa o repository com a sessão do banco."""
        self.db = db

    def criar(self, funcionario: Funcionario) -> Funcionario:
        """Persiste um novo funcionário."""
        self.db.add(funcionario)
        self.db.commit()
        self.db.refresh(funcionario)
        return funcionario

    def listar(self, skip: int = 0, limit: int = 50) -> list[Funcionario]:
        """Lista funcionários ativos com paginação (nome ASC)."""
        return (
            self.db.query(Funcionario)
            .filter(Funcionario.ativo.is_(True))
            .order_by(Funcionario.nome.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def buscar_por_id(self, funcionario_id: int) -> Optional[Funcionario]:
        """Busca funcionário ativo pelo identificador."""
        return (
            self.db.query(Funcionario)
            .filter(
                Funcionario.id == funcionario_id,
                Funcionario.ativo.is_(True),
            )
            .first()
        )

    def buscar_por_cpf(self, cpf: str) -> Optional[Funcionario]:
        """Busca funcionário ativo pelo CPF."""
        return (
            self.db.query(Funcionario)
            .filter(
                Funcionario.cpf == cpf,
                Funcionario.ativo.is_(True),
            )
            .first()
        )

    def atualizar(self, funcionario: Funcionario) -> Funcionario:
        """Persiste alterações em um funcionário existente."""
        self.db.commit()
        self.db.refresh(funcionario)
        return funcionario

    def inativar(self, funcionario: Funcionario) -> Funcionario:
        """
        Realiza exclusão lógica (soft delete).

        Nunca remove o registro fisicamente.
        """
        funcionario.ativo = False
        self.db.commit()
        self.db.refresh(funcionario)
        return funcionario
