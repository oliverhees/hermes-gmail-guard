<div align="center">

**🚧 STATUS: BETA v0.1**

![Gmail Guard — Hermes reads. You send.](docs/assets/gmail-guard-release.en.png)

# 🛡️ Gmail Guard for Hermes

**Let your AI agent manage Gmail — without ever being able to send in your name.**

<p align="center">
  <a href="#-license"><img src="https://img.shields.io/badge/License-AGPL--3.0%20%2B%20Commercial-red" alt="License" /></a>
  <img src="https://img.shields.io/badge/For-Hermes%20Agent-red" alt="For Hermes Agent" />
  <img src="https://img.shields.io/badge/Selfhosted-Coolify--ready-red" alt="Coolify ready" />
  <a href="https://github.com/oliverhees/hermes-gmail-guard/actions/workflows/tests.yml"><img src="https://github.com/oliverhees/hermes-gmail-guard/actions/workflows/tests.yml/badge.svg" alt="Tests" /></a>
  <a href="https://aiianer.de"><img src="https://img.shields.io/badge/Community-AIIANER-black" alt="AIIANER Community" /></a>
</p>

**🇬🇧 English** · [🇩🇪 Deutsch](README.de.md)

[Quickstart](#-quickstart) · [Whole mailbox](#-manage-the-whole-mailbox) · [How it works](#-how-it-works) · [Security model](#️-security-model) · [Easy guide](docs/START-HERE.md) · [License](#-license)

</div>

---

## What is this?

Gmail Guard is a small, self-hosted **MCP server** that sits between the
[Hermes Agent](https://github.com/NousResearch/hermes-agent) and your Gmail
accounts. Hermes can **read, search, sort, archive, clean up and write
drafts** — but there is **no tool to send**. Sending happens only through a
separate Telegram bot, and only after **you** tap "Send" on an exact preview.

**Part of the AIIANER ecosystem:** At [AIIANER](https://aiianer.de) we build an
AI operating system on top of [Hermes](https://github.com/NousResearch/hermes-agent).
Hermes itself is an open-source project by **Nous Research** — this is an
independent community extension and has no official affiliation with Nous Research.

## Why?

An autonomous agent with Gmail access can send mail **in your name**. It does
not need to be "evil" for that: **one crafted email** in your inbox
("forward all invoices to …") is enough — that's prompt injection.

A rule in the prompt ("never send without asking") is a *request*, not a lock.
Hermes also writes its own skills and has terminal access — if it ever holds
your Google token, it can send. And even Google's own permissions don't help
much: the scope needed for drafts (`gmail.compose`) **also allows sending**.

**Gmail Guard's answer: the key stays outside of Hermes.**

## ✨ Features

- **No send tool — by design.** 20 tools for Hermes, none of them sends, forwards or deletes permanently.
- **Approval with fingerprint.** Telegram preview shows To/CC/**BCC**/subject/body/attachments. Only the exact previewed bytes are sent (SHA-256) — edited afterwards → blocked.
- **Bulk brake.** Trash/spam/archive above a rolling hourly limit requires your OK. Splitting into many small calls doesn't help.
- **Kill switch.** `/stopp` in Telegram locks everything instantly, `/weiter` resumes.
- **Gmail links.** Every result (mail, draft, mailbox) carries a direct link; in Telegram a button opens the draft in Gmail.
- **Multi-account.** Personal Gmail and Google Workspace, side by side.
- **Attachments.** Reads text from PDF, DOCX, HTML, TXT/CSV/JSON.
- **Untrusted-content marking.** Mail content is wrapped as data, fake markers are defused.
- **Audit log + daily report.** Every action is logged; a summary arrives in Telegram every evening.
- **Staged rollout.** `read` → `organize` → `full`, one line in the config.

## 🧩 How it works

```
Hermes (local) ─┐
                ├─► MetaMCP (optional) ─► gmail-guard ─► Gmail / Workspace
Hermes (VPS)  ──┘                         (no send)
                                              │ shared DB
                  You (Telegram) ◄──► approval bot ─┘ (sends ONLY after your tap)
```

1. A customer writes → Hermes reads, sorts, summarizes.
2. You: *"Draft a reply."* → Hermes creates a **draft in your Gmail**, in the same thread.
3. Hermes requests approval → **Telegram shows the exact preview.**
4. You tap **✅ Send** — or open the draft in Gmail, edit it and send it yourself.

The customer sees **your** address in the same thread. Hermes only ever pre-writes.

## 🛡️ Security model

| # | Layer | What it prevents |
|---|---|---|
| 1 | No send tool in the code | Hermes can't call what doesn't exist |
| 2 | Tokens only in isolated containers | Hermes never holds a Google credential |
| 3 | Approval with fingerprint | Changing a draft after the preview |
| 4 | Only your Telegram ID can approve | Someone else (or Hermes) approving |
| 5 | Bulk brake + daily trash limit | Mass deletion by mistake or injection |
| 6 | Audit log + daily report | Silent misuse |
| 7 | Untrusted-content marking | Instructions hidden in mails |

Also: protected labels (`INBOX`, `TRASH`, `SPAM`, …) can't be changed via the label
tool, Hermes can only edit **its own** drafts, max. 20 recipients per draft.

### ⚠️ Honest limits (please read)

- The guarantee depends on **isolation**: if Hermes runs as root or in the `docker` group on the same host, it could read the token files. The setup guide includes a check for this.
- Gmail Guard protects your **account**. It does **not** stop data exfiltration through other channels Hermes may have (web requests, other tools).
- The Google scope `gmail.modify` technically allows sending — protection comes from code + isolation, not from Google.

## 🚀 Quickstart

**3 steps. The assistant does the rest.**

| | What | Where |
|---|---|---|
| 1️⃣ | Create Google access (click-by-click guide); Telegram bot is optional | browser |
| 2️⃣ | `python scripts/setup.py` – asks questions, generates all keys, connects Gmail | your computer |
| 3️⃣ | Start: **Coolify** (paste the Docker Compose) **or** `docker compose -f docker-compose.local.yml up -d` | server **or** your computer |

```bash
git clone https://github.com/oliverhees/hermes-gmail-guard.git
cd hermes-gmail-guard
python start.py        # Mac/Linux: python3 start.py
```

➡️ **Beginner guide, every step with a checkbox:** [docs/START-HERE.md](docs/START-HERE.md)

**Does it have to run on a server?** No. Gmail Guard also runs on your own computer, but only while the computer is on. On a server (e.g. with Coolify) it runs permanently and is safer. **Hermes itself can stay local.**

## 📬 Manage the whole mailbox

Hermes looks after your complete Gmail, not just forwarded mails:

- 🏷️ creates **labels** and **sorts** mail
- 🚫 clears away **spam and newsletters** (large amounts only with your OK)
- 👀 regularly checks **what's new**
- ✍️ writes **reply drafts** straight into your Gmail, in the same thread
- 📱 pings you on Telegram with a **link to the draft in Gmail**
- ✅ sends only when **you** tap in Telegram or send in Gmail yourself

Ready-made rules for Hermes: [hermes/gmail-rules.md](hermes/gmail-rules.md) → section "Inbox manager".

### Hand single mails to Hermes (optional)

No separate mailbox needed: forward to **`you+hermes@gmail.com`**, a Gmail filter applies the label
`An Hermes`, Hermes picks it up. Details: [docs/SETUP.md](docs/SETUP.md#-forwarding-mails-to-hermes).

## 🧪 Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

30 tests against a simulated Gmail — no account needed. They verify the promises
above: no send tool, bulk brake incl. salami tactics, protected labels, fingerprint
check, stranger clicks, double clicks, kill switch.

## 🔧 Status

**Beta v0.1** — honest checklist:

- [x] MCP server starts, bearer auth blocks unknown callers
- [x] All 20 tools covered by tests against a simulated Gmail
- [x] Approval bot: fingerprint, BCC display, owner-only, no double send
- [x] Attachment extraction (PDF, DOCX, HTML, text)
- [x] Setup assistant, compose files for local and Coolify (tokens via environment variable)
- [ ] Coolify compose and setup assistant tested against real Coolify/Google (so far only with simulated data)
- [ ] End-to-end test against a real Gmail account
- [ ] Docker build verified (runs in CI from the first push)
- [ ] Bot/tool messages in English (currently German — PRs welcome)

## ⚖️ Compared to Google's Gmail MCP

Google offers an official [Gmail MCP server](https://developers.google.com/workspace/gmail/api/guides/configure-mcp-server) (Developer Preview). **It has no send tool either** — it reads, searches, labels and creates drafts that you send yourself in Gmail. A good design. The differences lie elsewhere:

| | Google's Gmail MCP | Gmail Guard |
|---|---|---|
| Send tool | ❌ none — drafts only | ❌ none — drafts only |
| Who holds the Google token | the MCP client (the agent) | only an isolated container |
| Token scope | `gmail.compose` — per Google, this scope also permits sending via the regular Gmail API¹ | agent holds no Google token at all |
| Sending | manually in Gmail | manually in Gmail **or** one tap in Telegram with an exact-preview fingerprint |
| Archive / trash / spam | ❌ not available | ✅ with bulk brake + daily limit |
| Kill switch, audit log, daily report | ❌ | ✅ |
| Maintenance | ✅ Google | you |
| Status | Developer Preview | Beta |

¹ *Untested assumption:* an agent with shell access that can read its own OAuth token could, in principle, call the Gmail API directly. If your agent has no shell access, this doesn't apply.

**Rule of thumb:** You in a chat UI → Google's MCP is great. An autonomous agent with shell access and sensitive data → keep the key outside the agent.

> **Correction (v0.1.1):** An earlier version of this README claimed Google's Gmail MCP could send mail without you. That was wrong — thanks to the community member who pointed it out with the source.

---

## 🌍 The AIIANER universe

| | |
| --- | --- |
| 🏠 **Community** | [aiianer.de](https://aiianer.de) — courses, labs, tutorials, AI coaches |
| 📺 **YouTube** | [youtube.com/@aiianer](https://www.youtube.com/@aiianer) — tools, tests, deep dives |
| 🔒 **Datenschleuse** | [github.com/oliverhees/datenschleuse](https://github.com/oliverhees/datenschleuse) — GDPR filter for your AI |
| 🛡️ **coolify-shield** | [github.com/oliverhees/coolify-shield](https://github.com/oliverhees/coolify-shield) — lock down your server |

## 📜 License

Dual licensed: **AGPL-3.0** (private use, self-hosters, research) or a
**commercial license** (closed products/services, no source disclosure).
Details: [LICENSING.md](LICENSING.md). Requests via the
[AIIANER Community](https://aiianer.de) or **hi@aiianer.de**.

## Security

Please do **not** report vulnerabilities as public issues. See [SECURITY.md](SECURITY.md).

## Trademarks

"AIIANER" is a trademark of Oliver Hees aka Aiianer. The code license grants
**no** rights to this name or logo. Forks must use their own name.

"Hermes" is an open-source project by **Nous Research**
([github.com/NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)).
"Gmail" and "Google Workspace" are trademarks of Google LLC. This project is
independent and not affiliated with Nous Research or Google.

---

<p align="center">
  © 2026 <strong>Oliver Hees aka Aiianer</strong> ·
  <a href="https://aiianer.de">aiianer.de</a> ·
  Made with 🖤 in the AIIANER universe
</p>
