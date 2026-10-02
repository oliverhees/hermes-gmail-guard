#!/usr/bin/env python3
"""Setup-Assistent: stellt dir Fragen, erzeugt alle Schlüssel, verbindet Gmail und schreibt die Einstellungen.

    python scripts/setup.py

Läuft auf deinem Rechner (braucht einen Browser für den Google-Login).
Nochmal starten = weiteres Gmail-Konto hinzufügen (Schlüssel bleiben gleich).

Ergebnis:
  out/settings.env   → alles für Coolify (komplett in "Environment Variables" einfügen)
  guard.env, bot.env → nur bei "Dieser Rechner" (für docker-compose.local.yml)
"""
import re
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cryptography.fernet import Fernet  # noqa: E402

from common.tokens import NAME_RE, SCOPE_COMPOSE, SCOPE_MODIFY, SCOPE_READ, encrypt_account  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MODES = {"1": "read", "2": "organize", "3": "full"}
GUARD_KEYS = ["GUARD_MODE", "APPROVAL_BOT", "GUARD_TOKEN_KEY", "MCP_BEARER_TOKEN", "GUARD_ACCOUNTS", "TZ"]
BOT_KEYS = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_ALLOWED_USER_ID", "BOT_TOKEN_KEY", "BOT_ACCOUNTS", "TZ"]


# ---------------------------------------------------------------- Ein-/Ausgabe
def ask(question, default=None, check=None):
    while True:
        shown = f" [{default}]" if default else ""
        answer = input(f"{question}{shown}: ").strip() or (default or "")
        if not answer:
            print("   ⚠️  Bitte etwas eingeben.")
        elif check and not check(answer):
            print("   ⚠️  Das sieht nicht richtig aus. Nochmal versuchen.")
        else:
            return answer


def read_env(path: Path) -> dict:
    out = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip()
    return out


def render_env(example: Path, values: dict, keys: list) -> str:
    """Vorlage (*.env.example) übernehmen und die eigenen Werte eintragen."""
    lines = []
    for line in example.read_text().splitlines():
        k = line.split("=", 1)[0].strip()
        lines.append(f"{k}={values[k]}" if "=" in line and k in keys and k in values else line)
    return "\n".join(lines) + "\n"


def write_secret(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(0o600)


# ---------------------------------------------------------------- Konten
def merge_account(blobs: str, key: str, name: str, new_blob: str) -> str:
    """Ersetzt ein Konto mit gleichem Namen, sonst hängt es hinten an."""
    import json

    f = Fernet(key.encode())
    kept = [b for b in blobs.split(",") if b.strip() and json.loads(f.decrypt(b.strip().encode()))["name"] != name]
    return ",".join(kept + [new_blob])


def connect(cfg, name, client_secret, mode, bot):
    from add_account import login  # erst hier: braucht die Google-Bibliotheken

    scopes = [SCOPE_READ] if mode == "read" else [SCOPE_MODIFY]
    creds, email = login(client_secret, scopes, "dem Konto, das Hermes verwalten soll")
    blob = encrypt_account(cfg["GUARD_TOKEN_KEY"], name, email, scopes, creds).decode()
    cfg["GUARD_ACCOUNTS"] = merge_account(cfg.get("GUARD_ACCOUNTS", ""), cfg["GUARD_TOKEN_KEY"], name, blob)
    print(f"✅ Hermes darf {email} verwalten ({mode}).")
    if mode == "full" and bot:
        print("\n2️⃣  Zweiter Login – für den Freigabe-Bot (nur Entwürfe + Senden nach deinem Tipp).")
        bot_creds, bot_email = login(client_secret, [SCOPE_COMPOSE], email)
        if bot_email != email:
            sys.exit(f"❌ Falsches Konto ({bot_email}). Bitte mit {email} anmelden – nochmal starten.")
        bot_blob = encrypt_account(cfg["BOT_TOKEN_KEY"], name, email, [SCOPE_COMPOSE], bot_creds).decode()
        cfg["BOT_ACCOUNTS"] = merge_account(cfg.get("BOT_ACCOUNTS", ""), cfg["BOT_TOKEN_KEY"], name, bot_blob)
        print(f"✅ Freigabe-Bot darf für {email} senden – aber nur nach deinem Tipp.")


# ---------------------------------------------------------------- Ablauf
def main(out=ROOT / "out"):
    settings = out / "settings.env"
    cfg = read_env(settings)
    again = bool(cfg.get("GUARD_TOKEN_KEY"))
    print("🛡️  Gmail Guard – Einrichtung" + (" (weiteres Konto)" if again else ""))
    print("Du beantwortest ein paar Fragen. Enter = Vorschlag übernehmen.\n")

    where = ask("1️⃣  Wo soll es laufen? 1 = Server (Coolify)  2 = Dieser Rechner", "1", lambda a: a in ("1", "2"))

    name = ask("2️⃣  Kurzname für das Konto (z.B. privat, firma)", "privat", NAME_RE.match)
    found = sorted(Path.cwd().glob("client_secret*.json"))
    secret = ask("3️⃣  Pfad zur Google-Datei client_secret….json", str(found[0]) if found else None,
                 lambda p: Path(p).expanduser().is_file())

    print("\n4️⃣  Was darf Hermes?\n"
          "   1 = nur lesen\n"
          "   2 = lesen + aufräumen (Labels, Archiv, Spam, Papierkorb)\n"
          "   3 = alles + Entwürfe schreiben (Empfohlen: ganzes Postfach verwalten)")
    mode = MODES[ask("   Deine Wahl", "3", lambda a: a in MODES)]
    cfg["GUARD_MODE"] = mode

    if "APPROVAL_BOT" not in cfg:
        cfg["APPROVAL_BOT"] = "0"
        if mode != "read":
            print("\n5️⃣  Wie willst du senden?\n"
                  "   1 = Nur in Gmail selbst (Hermes legt Entwürfe an + schickt dir den Link) – einfach\n"
                  "   2 = Zusätzlich per Tipp in Telegram (braucht einen eigenen Telegram-Bot)")
            if ask("   Deine Wahl", "1", lambda a: a in ("1", "2")) == "2":
                cfg["APPROVAL_BOT"] = "1"
    bot = cfg["APPROVAL_BOT"] == "1"
    if bot and not cfg.get("TELEGRAM_BOT_TOKEN"):
        print("\n   Telegram-Freigabe-Bot (ein NEUER Bot über @BotFather, nicht der von Hermes!)")
        cfg["TELEGRAM_BOT_TOKEN"] = ask("   Bot-Token (sieht aus wie 123456:ABC…)", None,
                                        lambda t: re.fullmatch(r"\d+:[\w-]{20,}", t))
        cfg["TELEGRAM_ALLOWED_USER_ID"] = ask("   Deine Telegram-User-ID (nur Zahlen, von @userinfobot)", None,
                                              str.isdigit)

    cfg.setdefault("GUARD_TOKEN_KEY", Fernet.generate_key().decode())
    if bot:
        cfg.setdefault("BOT_TOKEN_KEY", Fernet.generate_key().decode())
    cfg.setdefault("MCP_BEARER_TOKEN", secrets.token_urlsafe(48))
    cfg.setdefault("TZ", "Europe/Berlin")

    connect(cfg, name, str(Path(secret).expanduser()), mode, bot)

    write_secret(settings, "\n".join(f"{k}={v}" for k, v in cfg.items()) + "\n")
    if where == "2":
        write_secret(ROOT / "guard.env", render_env(ROOT / "guard.env.example", cfg, GUARD_KEYS))
        if bot:
            write_secret(ROOT / "bot.env", render_env(ROOT / "bot.env.example", cfg, BOT_KEYS))

    print("\n🎉 Fertig!\n")
    if where == "1":
        print(f"📄 Deine Einstellungen: {settings}\n"
              "   → Datei öffnen, ALLES kopieren, in Coolify bei 'Environment Variables'\n"
              + ("     Compose-Datei: /docker-compose.coolify.bot.yml\n" if bot else "     Compose-Datei: /docker-compose.coolify.yml\n") +
              "     (Developer view) einfügen und speichern. Dann 'Deploy'.\n"
              "🔐 Die Datei enthält Geheimnisse: nicht teilen, nicht in Git. Nach dem Einfügen löschen\n"
              "   oder im Passwortmanager ablegen (du brauchst sie nur für weitere Konten).")
    else:
        print("📄 guard.env und bot.env sind geschrieben.\n"
              "   → Starten:  docker compose -f docker-compose.local.yml " + ("-f docker-compose.local.bot.yml " if bot else "") + "up -d --build\n"
              "🔐 Die Dateien enthalten Geheimnisse: nicht teilen, nicht in Git.")
    print("\n➕ Weiteres Konto? Dieses Programm einfach nochmal starten.")


if __name__ == "__main__":
    main()
