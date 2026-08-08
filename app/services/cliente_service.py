"""
Service de Cliente — regras de negócio (COMMIT 0008).

Não lança HTTPException. Exceções de domínio são mapeadas na API.
No futuro existirá um middleware/handler global de exceções.
"""

from typing import Any
from typing import Optional

from app.models.cliente import Cliente
from app.repositories.cliente_repository import ClienteRepository
from app.schemas.cliente import ClienteCreate
from app.schemas.cliente import ClienteUpdate


class ClienteNaoEncontrado(Exception):
    """Cliente ativo não encontrado."""


class ClienteDuplicado(Exception):
    """Cliente com CPF/CNPJ já cadastrado."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ClienteService:
    """Regras de negócio do cadastro de clientes."""

    def __init__(self, repository: ClienteRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository

    def criar(self, dados: ClienteCreate) -> Cliente:
        """Cria um novo cliente validando unicidade de CPF/CNPJ."""
        self._validar_cpf_cnpj_unico(dados.cpf_cnpj)

        cliente = Cliente(**dados.model_dump())
        return self.repository.criar(cliente)

    def listar(self, skip: int = 0, limit: int = 50) -> list[Cliente]:
        """Lista clientes ativos com paginação."""
        return self.repository.listar(skip=skip, limit=limit)

    def buscar_por_id(self, cliente_id: int) -> Cliente:
        """Retorna cliente ativo por id ou levanta ClienteNaoEncontrado."""
        cliente = self.repository.buscar_por_id(cliente_id)

        if cliente is None:
            raise ClienteNaoEncontrado("Cliente não encontrado.")

        return cliente

    def atualizar(
        self,
        cliente_id: int,
        dados: ClienteUpdate,
    ) -> Cliente:
        """Atualiza campos informados do cliente (exclude_unset)."""
        cliente = self.buscar_por_id(cliente_id)
        campos: dict[str, Any] = dados.model_dump(exclude_unset=True)

        if "cpf_cnpj" in campos:
            self._validar_cpf_cnpj_unico(
                campos["cpf_cnpj"],
                cliente_id=cliente_id,
            )

        for campo, valor in campos.items():
            setattr(cliente, campo, valor)

        return self.repository.atualizar(cliente)

    def excluir(self, cliente_id: int) -> Cliente:
        """Realiza exclusão lógica do cliente (ativo = False)."""
        cliente = self.buscar_por_id(cliente_id)
        return self.repository.inativar(cliente)

    def _validar_cpf_cnpj_unico(
        self,
        cpf_cnpj: str,
        cliente_id: Optional[int] = None,
    ) -> None:
        """Valida se o CPF/CNPJ já está em uso por outro cliente ativo."""
        existente = self.repository.buscar_por_cpf_cnpj(cpf_cnpj)

        if existente is not None and existente.id != cliente_id:
            raise ClienteDuplicado(
                "Já existe um cliente cadastrado com este CPF/CNPJ."
            )
