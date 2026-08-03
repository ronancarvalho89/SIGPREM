from sqlalchemy.orm import Session

from app.models.cliente import Cliente


class ClienteRepository:

    def __init__(self, db: Session):

        self.db = db

    def criar(self, cliente: Cliente):

        self.db.add(cliente)

        self.db.commit()

        self.db.refresh(cliente)

        return cliente

    def listar(self):

        return (
            self.db
            .query(Cliente)
            .filter(Cliente.ativo == True)
            .order_by(Cliente.razao_social)
            .all()
        )