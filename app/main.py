from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import APP_NAME
from app.database.seed import executar_seed


@asynccontextmanager
async def lifespan(app: FastAPI):

    executar_seed()

    yield


app = FastAPI(
    title=APP_NAME,
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/")
def home():

    return {
        "sistema": APP_NAME,
        "status": "online",
        "versao": "0.1.0"
    }


from app.api.auth import router as auth_router
from app.api.clientes import router as clientes_router
from app.api.produtos import router as produtos_router
from app.api.fornecedores import router as fornecedores_router
from app.api.funcionarios import router as funcionarios_router
from app.api.compras_concreto import router as compras_concreto_router
from app.api.producao import router as producao_router
from app.api.dashboard import router as dashboard_router
from app.api.vendas import router as vendas_router
from app.api.movimentos_estoque import router as movimentos_estoque_router
from app.api.funcionarios_valor_produto import (
    router as funcionarios_valor_produto_router,
)
from app.api.movimentos_financeiros import (
    router as movimentos_financeiros_router,
)
from app.api.itens_venda import router as itens_venda_router
from app.api.financeiro import router as financeiro_router

app.include_router(auth_router)
app.include_router(clientes_router)
app.include_router(produtos_router)
app.include_router(fornecedores_router)
app.include_router(funcionarios_router)
app.include_router(compras_concreto_router)
app.include_router(producao_router)
app.include_router(dashboard_router)
app.include_router(vendas_router)
app.include_router(movimentos_estoque_router)
app.include_router(funcionarios_valor_produto_router)
app.include_router(movimentos_financeiros_router)
app.include_router(itens_venda_router)
app.include_router(financeiro_router)
