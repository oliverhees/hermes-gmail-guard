#!/usr/bin/env python3
"""Erzeugt alle Schlüssel auf einmal. Ausgabe in einen Passwortmanager kopieren!"""
import secrets

from cryptography.fernet import Fernet

print("# ---- guard.env ----")
print(f"GUARD_TOKEN_KEY={Fernet.generate_key().decode()}")
print(f"MCP_BEARER_TOKEN={secrets.token_urlsafe(48)}")
print("\n# ---- bot.env ----")
print(f"BOT_TOKEN_KEY={Fernet.generate_key().decode()}")
print("\n# Zwei VERSCHIEDENE Schlüssel = ein Leck öffnet nie beide Tresore.")
