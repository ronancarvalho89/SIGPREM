"""
Service de Produto — regras de negócio (COMMIT 0003).

Não lança HTTPException. Exceções de domínio são mapeadas na API.
No futuro existirá um middleware/handler global de exceções.

TODO(SIGPREM-002): futura alteração de modelo para referencia.
TODO(SIGPREM-003): validação de unidade quando existir produção.
"""

from typing import Any
from typing import Optional

from app.models.produto import Produto
from app.repositories.produto_repository import ProdutoRepository
from app.schemas.produto import ProdutoCreate
from app.schemas.produto import ProdutoUpdate


class ProdutoNaoEncontrado(Exception):
    """Produto ativo não encontrado."""


class ProdutoDuplicado(Exception):
    """Produto com código ou descrição já cadastrados."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class CategoriaNaoPodeSerAlterada(Exception):
    """Categoria do produto é imutável após o cadastro."""


class UnidadeNaoPodeSerAlterada(Exception):
    """Unidade não pode ser alterada quando há produção vinculada."""


class ProdutoService:
    """Regras de negócio do cadastro de produtos."""

    def __init__(self, repository: ProdutoRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository

    def criar(self, dados: ProdutoCreate) -> Produto:
        """Cria um novo produto validando unicidade de código e descrição."""
        self._validar_codigo_unico(dados.codigo)
        self._validar_descricao_unica(dados.descricao)

        produto = Produto(**dados.model_dump())
        return self.repository.criar(produto)

    def listar(self, skip: int = 0, limit: int = 50) -> list[Produto]:
        """Lista produtos ativos com paginação."""
        return self.repository.listar(skip=skip, limit=limit)

    def buscar_por_id(self, produto_id: int) -> Produto:
        """Retorna produto ativo por id ou levanta ProdutoNaoEncontrado."""
        produto = self.repository.buscar_por_id(produto_id)

        if produto is None:
            raise ProdutoNaoEncontrado("Produto não encontrado.")

        return produto

    def buscar_por_codigo(self, codigo: str) -> Produto:
        """Retorna produto ativo por código ou levanta ProdutoNaoEncontrado."""
        produto = self.repository.buscar_por_codigo(codigo)

        if produto is None:
            raise ProdutoNaoEncontrado("Produto não encontrado.")

        return produto

    def atualizar(self, produto_id: int, dados: ProdutoUpdate) -> Produto:
        """
        Atualiza campos permitidos do produto.

        categoria e codigo não podem ser alterados.
        unidade só pode ser alterada se não houver produção vinculada.
        """
        produto = self.buscar_por_id(produto_id)
        campos: dict[str, Any] = dados.model_dump(exclude_unset=True)

        if "categoria" in campos:
            raise CategoriaNaoPodeSerAlterada(
                "A categoria do produto não pode ser alterada."
            )

        if "descricao" in campos:
            self._validar_descricao_unica(
                campos["descricao"],
                produto_id=produto_id,
            )

        if "unidade" in campos and campos["unidade"] != produto.unidade:
            # TODO(SIGPREM-003): validação de unidade quando existir produção
            if self.repository.possui_producao(produto_id):
                raise UnidadeNaoPodeSerAlterada(
                    "A unidade não pode ser alterada pois o produto "
                    "já foi utilizado em produção."
                )

        for campo, valor in campos.items():
            setattr(produto, campo, valor)

        return self.repository.atualizar(produto)

    def excluir(self, produto_id: int) -> Produto:
        """Realiza exclusão lógica do produto (ativo = False)."""
        produto = self.buscar_por_id(produto_id)
        return self.repository.inativar(produto)

    def _validar_codigo_unico(
        self,
        codigo: str,
        produto_id: Optional[int] = None,
    ) -> None:
        """Valida se o código já está em uso por outro produto ativo."""
        existente = self.repository.buscar_por_codigo(codigo)

        if existente is not None and existente.id != produto_id:
            raise ProdutoDuplicado(
                "Já existe um produto cadastrado com este código."
            )

    def _validar_descricao_unica(
        self,
        descricao: str,
        produto_id: Optional[int] = None,
    ) -> None:
        """Valida se a descrição já está em uso por outro produto ativo."""
        existente = self.repository.buscar_por_descricao(descricao)

        if existente is not None and existente.id != produto_id:
            raise ProdutoDuplicado(
                "Já existe um produto com esta descrição."
            )
