"""Verschlüsselte Google-Tokens (eine Datei pro Konto: <name>.enc)."""
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")

SCOPE_READ = "https://www.googleapis.com/auth/gmail.readonly"
SCOPE_MODIFY = "https://www.googleapis.com/auth/gmail.modify"
SCOPE_COMPOSE = "https://www.googleapis.com/auth/gmail.compose"


@dataclass
class Account:
    name: str
    email: str
    scopes: list = field(default_factory=list)
    creds: Credentials = None

    @property
    def can_modify(self):
        return SCOPE_MODIFY in self.scopes


def _fernet(key_env):
    key = os.environ.get(key_env, "").strip()
    if not key:
        raise SystemExit(f"Umgebungsvariable {key_env} fehlt (Fernet-Schlüssel).")
    return Fernet(key.encode())


def encrypt_account(key: str, name: str, email: str, scopes: list, creds: Credentials) -> bytes:
    payload = {"name": name, "email": email, "scopes": scopes, "creds": json.loads(creds.to_json())}
    return Fernet(key.encode()).encrypt(json.dumps(payload).encode())


def load_accounts(tokens_dir: str, key_env: str) -> dict:
    f = _fernet(key_env)
    accounts = {}
    for p in sorted(Path(tokens_dir).glob("*.enc")):
        info = json.loads(f.decrypt(p.read_bytes()))
        name = info["name"]
        if not NAME_RE.match(name):
            raise SystemExit(f"Ungültiger Kontoname in {p.name}")
        creds = Credentials.from_authorized_user_info(info["creds"], info["scopes"])
        accounts[name] = Account(name=name, email=info["email"], scopes=info["scopes"], creds=creds)
    return accounts
