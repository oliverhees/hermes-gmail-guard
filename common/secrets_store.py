"""Schlüssel, die der Server beim ersten Start selbst erzeugt und im Volume merkt.

Damit muss niemand Schlüssel von Hand erzeugen oder einfügen: Fehlt GUARD_TOKEN_KEY oder
MCP_BEARER_TOKEN in der Umgebung, wird der Wert aus SECRETS_FILE gelesen (oder neu erzeugt).
"""
import json
import os
import secrets
from pathlib import Path

from cryptography.fernet import Fernet

GENERATORS = {
    "GUARD_TOKEN_KEY": lambda: Fernet.generate_key().decode(),
    "MCP_BEARER_TOKEN": lambda: secrets.token_urlsafe(48),
}


def ensure(names=("GUARD_TOKEN_KEY", "MCP_BEARER_TOKEN"), path=None):
    missing = [n for n in names if not os.environ.get(n, "").strip()]
    if not missing:
        return
    path = Path(path or os.environ.get("SECRETS_FILE", "/data/secrets.json"))
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        data = {}
    changed = False
    for n in missing:
        if not data.get(n):
            data[n], changed = GENERATORS[n](), True
        os.environ[n] = data[n]
    if changed:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data))
            path.chmod(0o600)
        except OSError as e:
            raise SystemExit(f"Kann {path} nicht speichern ({e}). Es muss ein beschreibbares Volume unter "
                             f"{path.parent} geben, sonst gehen Schlüssel beim Neustart verloren.") from None
