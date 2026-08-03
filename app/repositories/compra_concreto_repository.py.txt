from sqlalchemy.orm import Session

from app.models.compra_concreto import CompraConcreto


class CompraConcretoRepository:

    def __init__(self, db: Session):

        self.db = db

    def salvar(self, compra: CompraConcreto):

        self.db.add(compra)

        self.db.commit()

        self.db.refresh(compra)

        return compra

    def listar(self):

        return (
            self.db.query(CompraConcreto)
            .filter(CompraConcreto.ativo == True)
            .all()
        )