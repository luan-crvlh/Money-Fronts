import argparse
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import date

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import SessionLocal
from app.security import zeroize_key
from app.seed import seed_default_categories
from app.routers import categories, accounts, transactions, budgets, dashboard, recurring
from app import crud
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("money_fronts")

def run_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    command.upgrade(config, "head")

@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    db = SessionLocal()
    try:
        seed_default_categories(db)
        today = date.today()
        crud.generate_recurring_transactions(db, today.month, today.year)
    finally:
        db.close()
    logger.info("Money Fronts backend pronto.")
    yield
    zeroize_key()
    logger.info("Sidecar encerrado, chave zerada da memória.")

# Única instância do FastAPI
app = FastAPI(title="Money Fronts API", version="0.1.0", lifespan=lifespan)

# CORS configurado para aceitar o Vite (localhost:5173) e o Tauri
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173", 
        "tauri://localhost", 
        "http://tauri.localhost"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Capturador Global de Erros (Evita o falso erro de CORS)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"ERRO FATAL NA ROTA: {exc}")
    traceback.print_exc() # Imprime o erro vermelho no terminal do Rust
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers={"Access-Control-Allow-Origin": "http://localhost:5173"}
    )

app.include_router(categories.router)
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(budgets.router)
app.include_router(dashboard.router)
app.include_router(recurring.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

def main():
    parser = argparse.ArgumentParser(description="Money Fronts backend sidecar")
    parser.add_argument("--port", type=int, default=settings.PORT, help="Porta do Uvicorn")
    args = parser.parse_args()

    port = args.port or 8756  
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support() 
    main()