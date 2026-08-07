"""
Service de Funcionário — regras de negócio (COMMIT 0005).

Não lança HTTPException. Exceções de domínio são mapeadas na API.
No futuro existirá um middleware/handler global de exceções.
"""

from typing import Any
from typing import Optional

from app.models.funcionario import Funcionario
from app.repositories.funcionario_repository import FuncionarioRepository
from app.schemas.funcionario import FuncionarioCreate
from app.schemas.funcionario import FuncionarioUpdate


class FuncionarioNaoEncontrado(Exception):
    """Funcionário ativo não encontrado."""


class FuncionarioDuplicado(Exception):
    """Funcionário com CPF já cadastrado."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class FuncionarioService:
    """Regras de negócio do cadastro de funcionários."""

    def __init__(self, repository: FuncionarioRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository

    def criar(self, dados: FuncionarioCreate) -> Funcionario:
        """Cria um novo funcionário validando unicidade de CPF."""
        self._validar_cpf_unico(dados.cpf)

        funcionario = Funcionario(**dados.model_dump())
        return self.repository.criar(funcionario)

    def listar(self, skip: int = 0, limit: int = 50) -> list[Funcionario]:
        """Lista funcionários ativos com paginação."""
        return self.repository.listar(skip=skip, limit=limit)

    def buscar_por_id(self, funcionario_id: int) -> Funcionario:
        """Retorna funcionário ativo por id ou levanta FuncionarioNaoEncontrado."""
        funcionario = self.repository.buscar_por_id(funcionario_id)

        if funcionario is None:
            raise FuncionarioNaoEncontrado("Funcionário não encontrado.")

        return funcionario

    def atualizar(
        self,
        funcionario_id: int,
        dados: FuncionarioUpdate,
    ) -> Funcionario:
        """Atualiza campos informados do funcionário (exclude_unset)."""
        funcionario = self.buscar_por_id(funcionario_id)
        campos: dict[str, Any] = dados.model_dump(exclude_unset=True)

        if "cpf" in campos:
            self._validar_cpf_unico(
                campos["cpf"],
                funcionario_id=funcionario_id,
            )

        for campo, valor in campos.items():
            setattr(funcionario, campo, valor)

        return self.repository.atualizar(funcionario)

    def excluir(self, funcionario_id: int) -> Funcionario:
        """Realiza exclusão lógica do funcionário (ativo = False)."""
        funcionario = self.buscar_por_id(funcionario_id)
        return self.repository.inativar(funcionario)

    def _validar_cpf_unico(
        self,
        cpf: str,
        funcionario_id: Optional[int] = None,
    ) -> None:
        """Valida se o CPF já está em uso por outro funcionário ativo."""
        existente = self.repository.buscar_por_cpf(cpf)

        if existente is not None and existente.id != funcionario_id:
            raise FuncionarioDuplicado(
                "Já existe um funcionário cadastrado com este CPF."
            )
