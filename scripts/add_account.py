#!/usr/bin/env python3
"""Gmail-Konto verbinden. Läuft EINMAL auf deinem Rechner (braucht einen Browser).

Beispiel:
  python add_account.py --name privat --client-secret client_secret_privat.json --mode full

--mode read      → gmail-guard bekommt NUR Lesezugriff (Google selbst sperrt alles andere)
--mode organize  → Lesen + Aufräumen (Labels, Archiv, Papierkorb, Spam)
--mode full      → wie organize + Entwürfe; zusätzlich ein Token für den Freigabe-Bot (Senden)

Ergebnis: verschlüsselte Dateien in ./out/guard-tokens/ und ./out/bot-tokens/
→ auf den VPS kopieren und danach HIER LÖSCHEN.
"""
import argparse
import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google_auth_oauthlib.flow import InstalledAppFlow  # noqa: E402
from googleapiclient.discovery import build  # noqa: E402

from common.tokens import NAME_RE, SCOPE_COMPOSE, SCOPE_MODIFY, SCOPE_READ, encrypt_account  # noqa: E402


def login(client_secret, scopes, hint):
    print(f"\n🌐 Browser öffnet sich – melde dich an mit: {hint}")
    print(f"   Angefragte Rechte: {', '.join(s.rsplit('/', 1)[-1] for s in scopes)}")
    flow = InstalledAppFlow.from_client_secrets_file(client_secret, scopes)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent",
                                  open_browser=True)
    if not creds.refresh_token:
        sys.exit("❌ Kein Refresh-Token erhalten. Zugriff unter myaccount.google.com/permissions entfernen und neu starten.")
    email = build("gmail", "v1", credentials=creds, cache_discovery=False) \
        .users().getProfile(userId="me").execute()["emailAddress"]
    return creds, email


def key(env):
    k = os.environ.get(env) or getpass.getpass(f"🔑 {env} (aus secrets.env): ")
    if not k.strip():
        sys.exit(f"❌ {env} fehlt.")
    return k.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="Kurzname, z.B. privat oder firma")
    ap.add_argument("--client-secret", required=True, help="OAuth-Client-JSON aus der Google Cloud Console")
    ap.add_argument("--mode", choices=["read", "organize", "full"], default="full")
    ap.add_argument("--out", default="out")
    a = ap.parse_args()

    if not NAME_RE.match(a.name):
        sys.exit("❌ Name nur Kleinbuchstaben, Zahlen, - und _ (max. 32 Zeichen).")

    out = Path(a.out)
    (out / "guard-tokens").mkdir(parents=True, exist_ok=True)

    guard_scopes = [SCOPE_READ] if a.mode == "read" else [SCOPE_MODIFY]
    creds, email = login(a.client_secret, guard_scopes, "dem Konto, das Hermes verwalten soll")
    p = out / "guard-tokens" / f"{a.name}.enc"
    p.write_bytes(encrypt_account(key("GUARD_TOKEN_KEY"), a.name, email, guard_scopes, creds))
    print(f"✅ gmail-guard-Token für {email} → {p}")

    if a.mode == "full":
        (out / "bot-tokens").mkdir(parents=True, exist_ok=True)
        print("\n2️⃣  Jetzt der zweite Login – für den Freigabe-Bot (nur Entwürfe + Senden).")
        bot_creds, bot_email = login(a.client_secret, [SCOPE_COMPOSE], email)
        if bot_email != email:
            sys.exit(f"❌ Falsches Konto ({bot_email}). Bitte mit {email} anmelden.")
        p2 = out / "bot-tokens" / f"{a.name}.enc"
        p2.write_bytes(encrypt_account(key("BOT_TOKEN_KEY"), a.name, email, [SCOPE_COMPOSE], bot_creds))
        print(f"✅ Freigabe-Bot-Token für {email} → {p2}")

    print("\n📦 Nächster Schritt: Dateien auf den VPS kopieren (siehe README, Schritt 5)")
    print("🧹 Danach hier löschen:  rm -rf", out)


if __name__ == "__main__":
    main()
