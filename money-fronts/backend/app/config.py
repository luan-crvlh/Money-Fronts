"""
Configurações centrais do backend.

Segue RNF01 (segurança criptográfica), RNF02 (offline-first) e RNF06
(desacoplamento). Nenhuma URL externa é chamada a partir daqui.
"""
import os
import sys
from pathlib import Path


def _app_data_dir() -> Path:
    """Retorna o diretório de dados do app, coerente por SO (sem dependências externas)."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = str(Path.home() / "Library" / "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    path = Path(base) / "money-fronts"
    path.mkdir(parents=True, exist_ok=True)
    return path


class Settings:
    # Nome do serviço usado no Keyring do SO (RNF03)
    KEYRING_SERVICE = "finance_app"
    KEYRING_USERNAME = "db_key"

    # Local do arquivo SQLite/SQLCipher (nunca em texto plano na rede - RNF01)
    APP_DATA_DIR = _app_data_dir()
    DATABASE_PATH = APP_DATA_DIR / "money_fronts.db"

    # Modo de desenvolvimento: usa sqlite puro quando pysqlcipher3 não está disponível
    # no ambiente local (ex.: dev em máquina sem toolchain SQLCipher).
    # Em build de produção (PyInstaller), DEV_PLAINTEXT_DB deve ser sempre "0".
    DEV_PLAINTEXT_DB = os.environ.get("MONEY_FRONTS_DEV_PLAINTEXT_DB", "0") == "1"

    # Host/porta do Uvicorn - a porta é recebida via CLI/env pelo Tauri (DAS seção 4)
    HOST = "127.0.0.1"
    PORT = int(os.environ.get("MONEY_FRONTS_PORT", "0"))  # 0 = escolhida dinamicamente

    # CORS estrito, conforme DAS seção 2
    ALLOWED_ORIGINS = [
        "http://localhost",
        "http://localhost:5173",  # dev server do Vite
        "tauri://localhost",
        "http://tauri.localhost",
    ]

    # Regra 50/30/20 (necessidades / desejos / investimentos-dívidas)
    BUDGET_RULE = {"needs": 0.50, "wants": 0.30, "savings": 0.20}


settings = Settings()
