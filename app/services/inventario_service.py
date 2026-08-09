"""
Service de Inventário — regras de negócio (COMMIT 0065).

Não lança HTTPException. Exceções de domínio são mapeadas na API.
No futuro existirá um middleware/handler global de exceções.
"""

from typing import Any

from app.models.inventario import Inventario
from app.repositories.inventario_repository import InventarioRepository
from app.schemas.inventario import InventarioCreate
from app.schemas.inventario import InventarioUpdate


class InventarioNaoEncontrado(Exception):
    """Inventário ativo não encontrado."""


class InventarioService:
    """Regras de negócio do cadastro de inventários."""

    def __init__(self, repository: InventarioRepository) -> None:
        """Inicializa o service com o repository."""
        self.repository = repository

    def criar(self, dados: InventarioCreate) -> Inventario:
        """Cria um novo inventário."""
        inventario = Inventario(**dados.model_dump())
        return self.repository.criar(inventario)

    def listar(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Inventario]:
        """Lista inventários ativos com paginação."""
        return self.repository.listar(skip=skip, limit=limit)

    def buscar_por_id(self, inventario_id: int) -> Inventario:
        """Retorna inventário ativo por id ou levanta exceção."""
        inventario = self.repository.buscar_por_id(inventario_id)

        if inventario is None:
            raise InventarioNaoEncontrado("Inventário não encontrado.")

        return inventario

    def atualizar(
        self,
        inventario_id: int,
        dados: InventarioUpdate,
    ) -> Inventario:
        """Atualiza campos informados do inventário (exclude_unset)."""
        inventario = self.buscar_por_id(inventario_id)
        campos: dict[str, Any] = dados.model_dump(exclude_unset=True)

        for campo, valor in campos.items():
            setattr(inventario, campo, valor)

        return self.repository.atualizar(inventario)

    def excluir(self, inventario_id: int) -> Inventario:
        """Realiza exclusão lógica do inventário (ativo = False)."""
        inventario = self.buscar_por_id(inventario_id)
        return self.repository.inativar(inventario)
