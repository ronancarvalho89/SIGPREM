"""
Repository de Produto — acesso a dados (COMMIT 0003).

Responsável exclusivamente por operações de persistência.
Não contém regras de negócio.

TODO(SIGPREM-001): futura migração Alembic.
TODO(SIGPREM-003): validação de unidade quando existir produção.
TODO(SIGPREM-004): índice parcial para Soft Delete.
"""

from typing import Optional

from sqlalchemy import inspect
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.produto import Produto


class ProdutoRepository:
    """Acesso ao banco de dados para a entidade Produto."""

    def __init__(self, db: Session) -> None:
        """Inicializa o repository com a sessão do banco."""
        self.db = db

    def criar(self, produto: Produto) -> Produto:
        """Persiste um novo produto."""
        self.db.add(produto)
        self.db.commit()
        self.db.refresh(produto)
        return produto

    def listar(self, skip: int = 0, limit: int = 50) -> list[Produto]:
        """Lista produtos ativos com paginação, ordenados por codigo ASC."""
        return (
            self.db.query(Produto)
            .filter(Produto.ativo.is_(True))
            .order_by(Produto.codigo.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def buscar_por_id(self, produto_id: int) -> Optional[Produto]:
        """Busca produto ativo pelo identificador."""
        return (
            self.db.query(Produto)
            .filter(
                Produto.id == produto_id,
                Produto.ativo.is_(True),
            )
            .first()
        )

    def buscar_por_codigo(self, codigo: str) -> Optional[Produto]:
        """Busca produto ativo pelo código."""
        return (
            self.db.query(Produto)
            .filter(
                Produto.codigo == codigo,
                Produto.ativo.is_(True),
            )
            .first()
        )

    def buscar_por_descricao(self, descricao: str) -> Optional[Produto]:
        """Busca produto ativo pela descrição."""
        return (
            self.db.query(Produto)
            .filter(
                Produto.descricao == descricao,
                Produto.ativo.is_(True),
            )
            .first()
        )

    def atualizar(self, produto: Produto) -> Produto:
        """Persiste alterações em um produto existente."""
        self.db.commit()
        self.db.refresh(produto)
        return produto

    def inativar(self, produto: Produto) -> Produto:
        """
        Realiza exclusão lógica (soft delete).

        Nunca remove o registro fisicamente.
        """
        produto.ativo = False
        self.db.commit()
        self.db.refresh(produto)
        return produto

    def possui_producao(self, produto_id: int) -> bool:
        """
        Indica se o produto já foi utilizado em produção.

        Usa consulta SQL direta para não carregar o model Producao
        no metadata (evita impacto no create_all de outros módulos).

        TODO(SIGPREM-003): validação de unidade quando existir produção.
        """
        inspector = inspect(self.db.get_bind())

        if "producoes" not in inspector.get_table_names():
            return False

        quantidade = self.db.execute(
            text(
                "SELECT COUNT(1) AS total FROM producoes "
                "WHERE produto_id = :produto_id AND ativo = 1"
            ),
            {"produto_id": produto_id},
        ).scalar()

        return bool(quantidade)
