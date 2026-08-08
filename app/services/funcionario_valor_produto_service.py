"""
Service de FuncionarioValorProduto — regras de negócio (COMMIT 0020).

Não lança HTTPException. Exceções de domínio são mapeadas na API.
No futuro existirá um middleware/handler global de exceções.
"""

from typing import Any
from typing import Optional

from app.models.funcionario_valor_produto import FuncionarioValorProduto
from app.repositories.funcionario_valor_produto_repository import (
    FuncionarioValorProdutoRepository,
)
from app.schemas.funcionario_valor_produto import FuncionarioValorProdutoCreate
from app.schemas.funcionario_valor_produto import FuncionarioValorProdutoUpdate


class FuncionarioValorProdutoNaoEncontrado(Exception):
    """Registro ativo de valor por funcionário/produto não encontrado."""


class FuncionarioValorProdutoDuplicado(Exception):
    """Já existe valor cadastrado para o funcionário e produto."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class FuncionarioValorProdutoService:
    """Regras de negócio do cadastro de valores por funcionário/produto."""

    def __init__(self, repository: FuncionarioValorProdutoRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository

    def criar(
        self,
        dados: FuncionarioValorProdutoCreate,
    ) -> FuncionarioValorProduto:
        """Cria registro validando unicidade funcionário/produto."""
        self._validar_funcionario_produto_unico(
            dados.funcionario_id,
            dados.produto_id,
        )

        registro = FuncionarioValorProduto(**dados.model_dump())
        return self.repository.criar(registro)

    def listar(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[FuncionarioValorProduto]:
        """Lista registros ativos com paginação."""
        return self.repository.listar(skip=skip, limit=limit)

    def buscar_por_id(self, registro_id: int) -> FuncionarioValorProduto:
        """Retorna registro ativo por id ou levanta exceção."""
        registro = self.repository.buscar_por_id(registro_id)

        if registro is None:
            raise FuncionarioValorProdutoNaoEncontrado(
                "Valor por funcionário/produto não encontrado."
            )

        return registro

    def atualizar(
        self,
        registro_id: int,
        dados: FuncionarioValorProdutoUpdate,
    ) -> FuncionarioValorProduto:
        """Atualiza campos informados do registro (exclude_unset)."""
        registro = self.buscar_por_id(registro_id)
        campos: dict[str, Any] = dados.model_dump(exclude_unset=True)

        funcionario_id = campos.get(
            "funcionario_id",
            registro.funcionario_id,
        )
        produto_id = campos.get("produto_id", registro.produto_id)

        if "funcionario_id" in campos or "produto_id" in campos:
            self._validar_funcionario_produto_unico(
                funcionario_id,
                produto_id,
                registro_id=registro_id,
            )

        for campo, valor in campos.items():
            setattr(registro, campo, valor)

        return self.repository.atualizar(registro)

    def excluir(self, registro_id: int) -> FuncionarioValorProduto:
        """Realiza exclusão lógica do registro (ativo = False)."""
        registro = self.buscar_por_id(registro_id)
        return self.repository.inativar(registro)

    def _validar_funcionario_produto_unico(
        self,
        funcionario_id: int,
        produto_id: int,
        registro_id: Optional[int] = None,
    ) -> None:
        """Valida se já existe valor ativo para o par funcionário/produto."""
        existente = self.repository.buscar_por_funcionario_produto(
            funcionario_id,
            produto_id,
        )

        if existente is not None and existente.id != registro_id:
            raise FuncionarioValorProdutoDuplicado(
                "Já existe um valor cadastrado para este "
                "funcionário e produto."
            )
