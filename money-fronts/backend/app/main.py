"""
Entrypoint do Sidecar Python (DAS seção 4).

- Uvicorn na interface de loopback (127.0.0.1), porta recebida via argumento
  de linha de comando --port ou variável de ambiente MONEY_FRONTS_PORT.
- CORS restrito a http://localhost, tauri://localhost e http://tauri.localhost.
- Endpoint /health usado pelo Tauri/frontend para o Health Check obrigatório
  (RN1 do ERSW) antes de exibir a interface ao utilizador.
- Ao encerrar (SIGTERM enviado pelo Rust ao fechar a janela), zera a chave
  criptográfica da memória (RN1).
"""
import argparse
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine, SessionLocal
from app.security import zeroize_key
from app.seed import seed_default_categories
from app.routers import categories, accounts, transactions, budgets, dashboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("money_fronts")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: cria tabelas (dev) e semeia categorias padrão (RF02).
    # Em produção, o schema é evoluído via Alembic (RN3 do ERSW).
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_default_categories(db)
    finally:
        db.close()
    logger.info("Money Fronts backend pronto.")

    yield

    # Shutdown: zeroização da chave em memória (mitigação cold boot attack).
    zeroize_key()
    logger.info("Sidecar encerrado, chave zerada da memória.")


app = FastAPI(title="Money Fronts API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories.router)
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(budgets.router)
app.include_router(dashboard.router)


@app.get("/health")
def health_check():
    """Usado pelo Tauri/frontend para confirmar HTTP 200 antes de exibir os painéis."""
    return {"status": "ok"}


def main():
    parser = argparse.ArgumentParser(description="Money Fronts backend sidecar")
    parser.add_argument("--port", type=int, default=settings.PORT, help="Porta do Uvicorn")
    args = parser.parse_args()

    port = args.port or 8756  # fallback fixo para execução manual em dev
    uvicorn.run(app, host=settings.HOST, port=port, log_level="info")


if __name__ == "__main__":
    main()
