"""Test setup: temporary DB, throwaway encryption keys and fake accounts.

Both services load their config at import time, so everything is prepared
here before any test module imports them.
"""
import os
import secrets
import sys
import tempfile
from pathlib import Path

from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "gmail-guard"), str(ROOT / "freigabe-bot"), str(Path(__file__).parent)]

from common.tokens import SCOPE_COMPOSE, SCOPE_MODIFY, encrypt_account  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="gmail-guard-test-"))
GUARD_KEY, BOT_KEY = Fernet.generate_key().decode(), Fernet.generate_key().decode()
(TMP / "guard").mkdir()
(TMP / "bot").mkdir()


def _creds(scope):
    return Credentials(token="t", refresh_token="r", client_id="c", client_secret="s",
                       token_uri="https://oauth2.googleapis.com/token", scopes=[scope])


(TMP / "guard" / "privat.enc").write_bytes(
    encrypt_account(GUARD_KEY, "privat", "oliver@example.com", [SCOPE_MODIFY], _creds(SCOPE_MODIFY)))
(TMP / "bot" / "privat.enc").write_bytes(
    encrypt_account(BOT_KEY, "privat", "oliver@example.com", [SCOPE_COMPOSE], _creds(SCOPE_COMPOSE)))

os.environ.update({
    "DB_PATH": str(TMP / "guard.db"),
    "GUARD_MODE": "full",
    "GUARD_TOKEN_KEY": GUARD_KEY,
    "BOT_TOKEN_KEY": BOT_KEY,
    "MCP_BEARER_TOKEN": secrets.token_urlsafe(48),
    "TELEGRAM_BOT_TOKEN": "123:test",
    "TELEGRAM_ALLOWED_USER_ID": "4242",
})
