"""
Service de Fornecedor — regras de negócio (COMMIT 0004).

Não lança HTTPException. Exceções de domínio são mapeadas na API.
No futuro existirá um middleware/handler global de exceções.
"""

from typing import Any
from typing import Optional

from app.models.fornecedor import Fornecedor
from app.repositories.fornecedor_repository import FornecedorRepository
from app.schemas.fornecedor import FornecedorCreate
from app.schemas.fornecedor import FornecedorUpdate


class FornecedorNaoEncontrado(Exception):
    """Fornecedor ativo não encontrado."""


class FornecedorDuplicado(Exception):
    """Fornecedor com CPF/CNPJ já cadastrado."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class FornecedorService:
    """Regras de negócio do cadastro de fornecedores."""

    def __init__(self, repository: FornecedorRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository

    def criar(self, dados: FornecedorCreate) -> Fornecedor:
        """Cria um novo fornecedor validando unicidade de CPF/CNPJ."""
        self._validar_cpf_cnpj_unico(dados.cpf_cnpj)

        fornecedor = Fornecedor(**dados.model_dump())
        return self.repository.criar(fornecedor)

    def listar(self, skip: int = 0, limit: int = 50) -> list[Fornecedor]:
        """Lista fornecedores ativos com paginação."""
        return self.repository.listar(skip=skip, limit=limit)

    def buscar_por_id(self, fornecedor_id: int) -> Fornecedor:
        """Retorna fornecedor ativo por id ou levanta FornecedorNaoEncontrado."""
        fornecedor = self.repository.buscar_por_id(fornecedor_id)

        if fornecedor is None:
            raise FornecedorNaoEncontrado("Fornecedor não encontrado.")

        return fornecedor

    def atualizar(
        self,
        fornecedor_id: int,
        dados: FornecedorUpdate,
    ) -> Fornecedor:
        """Atualiza campos informados do fornecedor (exclude_unset)."""
        fornecedor = self.buscar_por_id(fornecedor_id)
        campos: dict[str, Any] = dados.model_dump(exclude_unset=True)

        if "cpf_cnpj" in campos:
            self._validar_cpf_cnpj_unico(
                campos["cpf_cnpj"],
                fornecedor_id=fornecedor_id,
            )

        for campo, valor in campos.items():
            setattr(fornecedor, campo, valor)

        return self.repository.atualizar(fornecedor)

    def excluir(self, fornecedor_id: int) -> Fornecedor:
        """Realiza exclusão lógica do fornecedor (ativo = False)."""
        fornecedor = self.buscar_por_id(fornecedor_id)
        return self.repository.inativar(fornecedor)

    def _validar_cpf_cnpj_unico(
        self,
        cpf_cnpj: str,
        fornecedor_id: Optional[int] = None,
    ) -> None:
        """Valida se o CPF/CNPJ já está em uso por outro fornecedor ativo."""
        existente = self.repository.buscar_por_cpf_cnpj(cpf_cnpj)

        if existente is not None and existente.id != fornecedor_id:
            raise FornecedorDuplicado(
                "Já existe um fornecedor cadastrado com este CPF/CNPJ."
            )
