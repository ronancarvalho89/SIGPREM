from app.models.cliente import Cliente

from app.repositories.cliente_repository import ClienteRepository


class ClienteService:

    def __init__(self, repository: ClienteRepository):

        self.repository = repository

    def criar(self, dados):

        cliente = Cliente(**dados.model_dump())

        return self.repository.criar(cliente)

    def listar(self):

        return self.repository.listar()