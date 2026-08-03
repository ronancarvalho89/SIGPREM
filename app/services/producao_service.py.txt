from decimal import Decimal

from app.models.producao import Producao
from app.models.compra_concreto import CompraConcreto
from app.models.produto import Produto

# estes dois modelos serão criados no próximo commit
# from app.models.movimento_estoque import MovimentoEstoque
# from app.models.funcionario_valor_produto import FuncionarioValorProduto


class SaldoConcretoInsuficiente(Exception):
    pass


class ProducaoService:

    def __init__(self, db):

        self.db = db

    def criar(self, dados):

        compra = self.db.get(
            CompraConcreto,
            dados.compra_concreto_id
        )

        produto = self.db.get(
            Produto,
            dados.produto_id
        )

        concreto = (
            Decimal(dados.quantidade_produzida)
            * Decimal(produto.concreto_por_unidade)
        )

        if compra.saldo < concreto:

            raise SaldoConcretoInsuficiente(
                "Saldo insuficiente de concreto."
            )

        compra.saldo -= concreto

        #
        # O cálculo do pagamento será substituído
        # pela tabela FuncionarioValorProduto
        #

        valor = Decimal("0.00")

        producao = Producao(

            data=dados.data,

            funcionario_id=dados.funcionario_id,

            produto_id=dados.produto_id,

            compra_concreto_id=dados.compra_concreto_id,

            quantidade_produzida=dados.quantidade_produzida,

            concreto_consumido=concreto,

            valor_producao=valor,

            observacao=dados.observacao

        )

        self.db.add(producao)

        #
        # Próximo commit:
        #
        # gerar entrada estoque
        # gerar pagamento funcionário
        #

        self.db.commit()

        self.db.refresh(producao)

        return producao