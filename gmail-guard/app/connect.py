"""Gmail-Konto direkt im Container verbinden – ohne Python, Browser-Programm oder Dateien auf deinem Rechner.

Aufruf im Terminal des Containers (Coolify → gmail-guard → Terminal):

    python -m app.connect            neues Konto verbinden
    python -m app.connect --show     MetaMCP-Schlüssel (Bearer-Token) anzeigen

Ablauf: Link öffnen (in irgendeinem Browser) → „Erlauben“ → die Seite lädt nicht (das ist richtig) →
komplette Adresse aus der Browserzeile hierher kopieren.
"""
import argparse
import os
import sys

from common import secrets_store
from common.tokens import NAME_RE, SCOPE_MODIFY, SCOPE_READ, encrypt_account

REDIRECT = "http://localhost:8080/"
AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"


def _make_flow(client_id, client_secret, scopes):
    from google_auth_oauthlib.flow import Flow
    config = {"installed": {"client_id": client_id, "client_secret": client_secret, "auth_uri": AUTH_URI,
                            "token_uri": TOKEN_URI, "redirect_uris": ["http://localhost"]}}
    flow = Flow.from_client_config(config, scopes=scopes, redirect_uri=REDIRECT)
    return flow


def _profile_email(creds):
    from googleapiclient.discovery import build
    return build("gmail", "v1", credentials=creds, cache_discovery=False) \
        .users().getProfile(userId="me").execute()["emailAddress"]


def main(argv=None, ask=input, out=print):
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true", help="MetaMCP-Schlüssel anzeigen")
    ap.add_argument("--name", help="Kurzname, z.B. privat")
    ap.add_argument("--mode", choices=["read", "organize", "full"],
                    default=os.environ.get("GUARD_MODE", "full"))
    a = ap.parse_args(argv)

    secrets_store.ensure()
    if a.show:
        out(f"MetaMCP-Bearer-Token: {os.environ['MCP_BEARER_TOKEN']}")
        return 0

    cid, csec = os.environ.get("GOOGLE_CLIENT_ID", "").strip(), os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
    if not cid or not csec:
        out("❌ GOOGLE_CLIENT_ID und GOOGLE_CLIENT_SECRET fehlen. Trage beide in Coolify unter "
            "Environment Variables ein (stehen in der heruntergeladenen client_secret…json) und starte neu.")
        return 1
    name = a.name or ask("Kurzname für das Konto [privat]: ").strip() or "privat"
    if not NAME_RE.match(name):
        out("❌ Name nur Kleinbuchstaben, Zahlen, - und _ (max. 32 Zeichen).")
        return 1

    scopes = [SCOPE_READ] if a.mode == "read" else [SCOPE_MODIFY]
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # nur für die Rückleitung auf localhost
    flow = _make_flow(cid, csec, scopes)
    url, _ = flow.authorization_url(access_type="offline", prompt="consent")
    out("\n1️⃣  Öffne diesen Link in deinem Browser (Testnutzer-Konto wählen):\n\n" + url + "\n")
    out("2️⃣  Klicke auf „Weiter“ / „Erlauben“. Danach zeigt der Browser eine Fehlerseite – das ist richtig.")
    out("3️⃣  Kopiere die KOMPLETTE Adresse aus der Browserzeile (beginnt mit http://localhost:8080/?state=…).\n")
    redirected = ask("Adresse hier einfügen: ").strip()
    try:
        flow.fetch_token(authorization_response=redirected)
    except Exception as e:  # noqa: BLE001 – Nutzer soll eine verständliche Meldung sehen
        out(f"❌ Das hat nicht geklappt ({type(e).__name__}). Nochmal starten und die ganze Adresse kopieren.")
        return 1
    creds = flow.credentials
    if not creds.refresh_token:
        out("❌ Kein Refresh-Token. Zugriff unter myaccount.google.com/permissions entfernen und nochmal starten.")
        return 1
    email = _profile_email(creds)

    tokens_dir = os.environ.get("TOKENS_DIR", "/data/tokens")
    os.makedirs(tokens_dir, exist_ok=True)
    path = os.path.join(tokens_dir, f"{name}.enc")
    with open(path, "wb") as f:
        f.write(encrypt_account(os.environ["GUARD_TOKEN_KEY"], name, email, scopes, creds))
    os.chmod(path, 0o600)
    out(f"\n✅ Hermes darf jetzt {email} verwalten ({a.mode}). Ein Neustart ist nicht nötig.")
    out("🔑 Deinen MetaMCP-Schlüssel zeigt:  python -m app.connect --show")
    return 0


if __name__ == "__main__":
    sys.exit(main())
