from sqlalchemy.orm import Session

from app.models.producao import Producao


class ProducaoRepository:

    def __init__(self, db: Session):

        self.db = db

    def salvar(self, producao: Producao):

        self.db.add(producao)

        self.db.commit()

        self.db.refresh(producao)

        return producao