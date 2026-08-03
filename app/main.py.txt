from fastapi import FastAPI

from app.core.config import APP_NAME

app = FastAPI(
    title=APP_NAME,
    version="0.1.0"
)


@app.get("/")
def home():

    return {
        "sistema": APP_NAME,
        "status": "online",
        "versao": "0.1.0"
    }


from app.api.clientes import router as clientes_router

app.include_router(clientes_router)