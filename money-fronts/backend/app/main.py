from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# --- ADICIONE ESTE BLOCO ---
app.add_middleware(
    CORSMiddleware,
    # Permite todas as origens (ideal para o Tauri dev e produção)
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------------------------

# O resto do seu código continua aqui (rotas, lifespans, etc)
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
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import SessionLocal
from app.security import zeroize_key
from app.seed import seed_default_categories
from app.routers import categories, accounts, transactions, budgets, dashboard, recurring
from app import crud
from datetime import date

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("money_fronts")


def run_migrations() -> None:
    """Atualiza o esquema local sem intervenção do usuário (RN3)."""
    from alembic import command
    from alembic.config import Config

    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    command.upgrade(config, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # RN3: migrações versionadas são aplicadas antes de acessar os dados.
    run_migrations()
    db = SessionLocal()
    try:
        seed_default_categories(db)
        # RF05: materializa os lançamentos previstos do mês, sem duplicá-los.
        today = date.today()
        crud.generate_recurring_transactions(db, today.month, today.year)
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
app.include_router(recurring.router)


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
