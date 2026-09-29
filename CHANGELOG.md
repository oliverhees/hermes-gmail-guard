# Changelog

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
