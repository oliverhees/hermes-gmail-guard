# Changelog

## Unreleased

- **Easy start / Einfacher Start:** `scripts/setup.py` assistant (asks questions, generates keys, connects Gmail, writes env files); new beginner guide `docs/START-HERE(.de).md` with a local-vs-server decision. / Setup-Assistent und neue Einsteiger-Anleitung mit Entscheidung lokal oder Server.
- **Login im Container / login inside the container:** `python -m app.connect` (link → allow → paste address); the server generates its own keys and stores them in a volume; new accounts are picked up without restart. Coolify needs only `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GUARD_MODE`. **Untested against real Google/Coolify/Docker.**
- **Telegram bot optional** (default: send in Gmail yourself); without it the bulk brake refuses instead of asking.
- **Coolify:** `docker-compose.coolify.yml`; Gmail accounts can now come from the environment variables `GUARD_ACCOUNTS` / `BOT_ACCOUNTS` instead of files. **Untested against a real Coolify.** / Gmail-Zugänge per Umgebungsvariable statt Dateien. Nicht gegen echtes Coolify getestet.
- **Local:** `docker-compose.local.yml` (port bound to 127.0.0.1) and `hermes/config-snippet.local.yaml`. / Lokaler Betrieb.
- **Gmail links:** tools return a direct link (mailbox, mail, thread, draft); the approval message opens the exact draft in Gmail; new bot command `/gmail`. / Direktlinks zu Gmail.
- **Inbox manager:** new section in `hermes/gmail-rules(.de).md` (label, sort, spam, reply drafts, Telegram report). / Regeln für „ganzes Postfach verwalten“.
- 9 new tests (links, env tokens, setup assistant). / 9 neue Tests.

## 0.1.1 — 2026-09-29

- **Docs fix / Korrektur:** Corrected the comparison with Google's official Gmail MCP — it has no send tool (drafts only). / Vergleich mit Googles offiziellem Gmail-MCP korrigiert: Er hat kein Senden-Werkzeug (nur Entwürfe).

## 0.1.0 — 2026-09-29 · Beta

First public release. / Erstes öffentliches Release.

- gmail-guard MCP server: 20 tools across three levels (`read`, `organize`, `full`) — no send tool
- Approval bot (Telegram): exact preview incl. BCC, SHA-256 fingerprint, owner-only, no double send
- Bulk brake (rolling hourly window) + daily trash limit, single-use bulk approvals
- Kill switch (`/stopp` / `/weiter`), audit log, daily report
- Multi-account (personal Gmail + Google Workspace), encrypted tokens (Fernet)
- Attachment text extraction (PDF, DOCX, HTML, text)
- 21 tests against a simulated Gmail
- Bilingual docs (EN/DE)
