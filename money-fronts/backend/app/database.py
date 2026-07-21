"""
Camada de persistência (DAS seção 5 / ERSW RNF01).

- SQLAlchemy 2.0 + SQLite protegido por SQLCipher (AES-256, page-level encryption).
- A chave nunca trafega em texto limpo na connection string: é injetada via
  evento `connect` do SQLAlchemy logo após a abertura do cursor (PRAGMA key).
- PRAGMA foreign_keys = ON é obrigatório no mesmo evento (RN2 do ERSW), pois o
  SQLite não ativa isso por padrão.

Modo de desenvolvimento (MONEY_FRONTS_DEV_PLAINTEXT_DB=1): usa sqlite padrão
sem SQLCipher, útil quando pysqlcipher3 não está compilado na máquina de dev.
Em produção este modo deve estar sempre desligado.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings
from app.security import get_or_create_db_key


class Base(DeclarativeBase):
    pass


def _build_engine():
    db_path = settings.DATABASE_PATH

    if settings.DEV_PLAINTEXT_DB:
        # Fallback de desenvolvimento: sqlite padrão (sem encriptação).
        url = f"sqlite:///{db_path}"
        engine = create_engine(url, connect_args={"check_same_thread": False})
    else:
        # Connection string exata definida no DAS: sqlite+pysqlcipher://
        url = f"sqlite+pysqlcipher://:x@/{db_path}?cipher=aes-256-cfb&kdf_iter=64000"
        engine = create_engine(url, connect_args={"check_same_thread": False})

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        if not settings.DEV_PLAINTEXT_DB:
            key = get_or_create_db_key()
            # Injeção da chave AES diretamente no ciclo de vida da conexão (DAS seção 5).
            cursor.execute(f"PRAGMA key = '{key}';")
        # RN2 do ERSW: chaves estrangeiras devem ser explicitamente ativadas.
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.close()

    return engine


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """Dependency do FastAPI: fornece uma sessão por requisição."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
