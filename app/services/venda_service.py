"""
Service de Venda — regras de negócio (COMMIT 0011).

Não lança HTTPException. Exceções de domínio são mapeadas na API.
No futuro existirá um middleware/handler global de exceções.
"""

from typing import Any
from typing import Optional
from uuid import UUID

from app.models.venda import Venda
from app.repositories.venda_repository import VendaRepository
from app.schemas.venda import VendaCreate
from app.schemas.venda import VendaUpdate


class VendaNaoEncontrada(Exception):
    """Venda ativa não encontrada."""


class VendaDuplicada(Exception):
    """Venda com número já cadastrado."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class VendaService:
    """Regras de negócio do cadastro de vendas."""

    def __init__(self, repository: VendaRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository

    def criar(self, dados: VendaCreate) -> Venda:
        """Cria uma nova venda validando unicidade do número."""
        self._validar_numero_unico(dados.numero)

        venda = Venda(**dados.model_dump())
        return self.repository.criar(venda)

    def listar(self, skip: int = 0, limit: int = 50) -> list[Venda]:
        """Lista vendas ativas com paginação."""
        return self.repository.listar(skip=skip, limit=limit)

    def buscar_por_id(self, venda_id: UUID) -> Venda:
        """Retorna venda ativa por id ou levanta VendaNaoEncontrada."""
        venda = self.repository.buscar_por_id(venda_id)

        if venda is None:
            raise VendaNaoEncontrada("Venda não encontrada.")

        return venda

    def atualizar(self, venda_id: UUID, dados: VendaUpdate) -> Venda:
        """Atualiza campos informados da venda (exclude_unset)."""
        venda = self.buscar_por_id(venda_id)
        campos: dict[str, Any] = dados.model_dump(exclude_unset=True)

        if "numero" in campos:
            self._validar_numero_unico(
                campos["numero"],
                venda_id=venda_id,
            )

        for campo, valor in campos.items():
            setattr(venda, campo, valor)

        return self.repository.atualizar(venda)

    def excluir(self, venda_id: UUID) -> Venda:
        """Realiza exclusão lógica da venda (ativo = False)."""
        venda = self.buscar_por_id(venda_id)
        return self.repository.inativar(venda)

    def _validar_numero_unico(
        self,
        numero: str,
        venda_id: Optional[UUID] = None,
    ) -> None:
        """Valida se o número já está em uso por outra venda ativa."""
        existente = self.repository.buscar_por_numero(numero)

        if existente is not None and existente.id != venda_id:
            raise VendaDuplicada(
                "Já existe uma venda cadastrada com este número."
            )
