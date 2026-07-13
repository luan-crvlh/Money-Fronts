"""
Gestão de segredos do Sistema Operativo (DAS seção 4 / ERSW RNF03).

Fluxo obrigatório:
1. Tenta obter a chave via keyring.get_password("finance_app", "db_key").
2. Se nula (primeira execução), gera uma chave AES-256 segura e persiste
   via keyring.set_password(...).

O processo Python é o único responsável por deter esta chave em memória.
A chave é zerada (best-effort) ao encerrar o processo (RN1 do ERSW).
"""
import secrets
import logging

import keyring

from app.config import settings

logger = logging.getLogger("money_fronts.security")

_cached_key: str | None = None


def get_or_create_db_key() -> str:
    """Recupera a chave do Keyring do SO ou gera/persiste uma nova (AES-256 / 32 bytes -> hex)."""
    global _cached_key
    if _cached_key is not None:
        return _cached_key

    key = keyring.get_password(settings.KEYRING_SERVICE, settings.KEYRING_USERNAME)

    if key is None:
        logger.info("Nenhuma chave encontrada no Keyring nativo. Gerando nova chave AES-256.")
        key = secrets.token_hex(32)  # 256 bits
        keyring.set_password(settings.KEYRING_SERVICE, settings.KEYRING_USERNAME, key)

    _cached_key = key
    return key


def zeroize_key() -> None:
    """Remove a chave da memória do processo (mitigação de cold boot attacks)."""
    global _cached_key
    _cached_key = None
