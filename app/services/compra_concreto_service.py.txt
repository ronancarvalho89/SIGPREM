from app.models.compra_concreto import CompraConcreto


class CompraConcretoService:

    def __init__(self, repository):

        self.repository = repository

    def criar(self, dados):

        compra = CompraConcreto(

            fornecedor_id=dados.fornecedor_id,

            data_compra=dados.data_compra,

            nota_fiscal=dados.nota_fiscal,

            quantidade_comprada=dados.quantidade_comprada,

            quantidade_recebida=dados.quantidade_recebida,

            saldo=dados.quantidade_recebida,

            valor_total=dados.valor_total,

            observacao=dados.observacao

        )

        return self.repository.salvar(compra)

    def listar(self):

        return self.repository.listar()