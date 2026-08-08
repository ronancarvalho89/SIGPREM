"""
Repository de FuncionarioValorProduto — acesso a dados (COMMIT 0020).

Responsável exclusivamente por operações de persistência.
Não contém regras de negócio.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.funcionario_valor_produto import FuncionarioValorProduto


class FuncionarioValorProdutoRepository:
    """Acesso ao banco de dados para FuncionarioValorProduto."""

    def __init__(self, db: Session) -> None:
        """Inicializa o repository com a sessão do banco."""
        self.db = db

    def criar(
        self,
        registro: FuncionarioValorProduto,
    ) -> FuncionarioValorProduto:
        """Persiste um novo valor por funcionário/produto."""
        self.db.add(registro)
        self.db.commit()
        self.db.refresh(registro)
        return registro

    def listar(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[FuncionarioValorProduto]:
        """Lista registros ativos com paginação (id DESC)."""
        return (
            self.db.query(FuncionarioValorProduto)
            .filter(FuncionarioValorProduto.ativo.is_(True))
            .order_by(FuncionarioValorProduto.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def buscar_por_id(
        self,
        registro_id: int,
    ) -> Optional[FuncionarioValorProduto]:
        """Busca registro ativo pelo identificador."""
        return (
            self.db.query(FuncionarioValorProduto)
            .filter(
                FuncionarioValorProduto.id == registro_id,
                FuncionarioValorProduto.ativo.is_(True),
            )
            .first()
        )

    def buscar_por_funcionario_produto(
        self,
        funcionario_id: int,
        produto_id: int,
    ) -> Optional[FuncionarioValorProduto]:
        """Busca registro ativo pela combinação funcionário/produto."""
        return (
            self.db.query(FuncionarioValorProduto)
            .filter(
                FuncionarioValorProduto.funcionario_id == funcionario_id,
                FuncionarioValorProduto.produto_id == produto_id,
                FuncionarioValorProduto.ativo.is_(True),
            )
            .first()
        )

    def atualizar(
        self,
        registro: FuncionarioValorProduto,
    ) -> FuncionarioValorProduto:
        """Persiste alterações em um registro existente."""
        self.db.commit()
        self.db.refresh(registro)
        return registro

    def inativar(
        self,
        registro: FuncionarioValorProduto,
    ) -> FuncionarioValorProduto:
        """
        Realiza exclusão lógica (soft delete).

        Nunca remove o registro fisicamente.
        """
        registro.ativo = False
        self.db.commit()
        self.db.refresh(registro)
        return registro
