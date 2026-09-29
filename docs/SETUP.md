# 🛡️ Gmail Guard – Full Setup Guide

**🇬🇧 English** · [🇩🇪 Deutsch](SETUP.de.md) · [← back to README](../README.md)

⏱️ **Time:** about 60–90 minutes for the first account, then about 5 minutes per additional account.

> ℹ️ The approval bot and the tool messages are currently in **German**. Bot commands: `/status`, `/heute` (today), `/stopp` (kill switch), `/weiter` (resume). English translations are welcome as PRs.

---

## 📋 Overview: 9 steps

| # | Step | Where | ✔ |
|---|---|---|---|
| 1 | Generate keys | laptop | ☐ |
| 2 | Set up Google Cloud | browser | ☐ |
| 3 | Create the Telegram approval bot | Telegram | ☐ |
| 4 | Connect an account | laptop | ☐ |
| 5 | Move to the server | VPS | ☐ |
| 6 | Start | VPS | ☐ |
| 7 | Connect Hermes (MetaMCP or direct) | VPS | ☐ |
| 8 | Configure Hermes | every Hermes machine | ☐ |
| 9 | Security check + tests | VPS | ☐ |

---

## 1️⃣ Generate keys

```bash
pip install -r scripts/requirements.txt
python scripts/gen_secrets.py
```

➡️ Put the output **into your password manager**:
- `GUARD_TOKEN_KEY` + `MCP_BEARER_TOKEN` → for gmail-guard
- `BOT_TOKEN_KEY` → for the approval bot

Two different keys on purpose: one leak never opens both vaults.

---

## 2️⃣ Set up Google Cloud

> Once per **account type**: one project for personal Gmail accounts, one per Workspace domain.

1. [console.cloud.google.com](https://console.cloud.google.com) → **New project**, e.g. `hermes-gmail-private`
2. **APIs & Services → Library →** "Gmail API" → **Enable**
3. **OAuth consent screen** (sometimes called "Google Auth Platform"):

| | 🏠 Personal @gmail.com | 🏢 Workspace |
|---|---|---|
| User type | **External** | **Internal** |
| Then | **Publish app → "In production"** ⚠️ | done |
| Why | In testing mode access **expires every 7 days** | Internal = no expiry |
| At login | "unverified app" warning → *Advanced → Continue* | no warning |

4. **Credentials → OAuth client ID →** type **Desktop app** → download the JSON, e.g. as `client_secret_private.json`

💡 **Workspace:** if the login is blocked, check *Security → API controls* in the Admin console.

---

## 3️⃣ Create the Telegram approval bot

⚠️ **A NEW bot, not the one Hermes uses!** Otherwise Hermes could read the approval messages.

1. In Telegram: `@BotFather` → `/newbot` → **copy the token**
2. Message `@userinfobot` → copy your **user ID** (a number)
3. Open your new bot and **press `/start`**. Without this it can't message you.

---

## 4️⃣ Connect an account (on your laptop, needs a browser)

```bash
export GUARD_TOKEN_KEY='...'   # from step 1
export BOT_TOKEN_KEY='...'

python scripts/add_account.py --name private --client-secret client_secret_private.json --mode full
```

- **Two logins** open one after the other: one for gmail-guard, one for the approval bot.
- Choose **the same account** both times.
- More accounts: same command, different `--name` (e.g. `work`).

| `--mode` | gmail-guard may | Lock |
|---|---|---|
| `read` | read only | 🔒 Google itself blocks everything else |
| `organize` | + clean up | code lock |
| `full` | + drafts, plus a bot token for sending | code lock |

💡 **Want to start extra carefully?** Connect with `--mode read` first, reconnect later with `full`.

---

## 5️⃣ Move to the server

```bash
# on the VPS
sudo mkdir -p /opt/gmail-guard && cd /opt/gmail-guard
sudo git clone https://github.com/oliverhees/hermes-gmail-guard.git .
sudo mkdir -p secrets/guard-tokens secrets/bot-tokens

# from your laptop
scp out/guard-tokens/*.enc root@VPS:/opt/gmail-guard/secrets/guard-tokens/
scp out/bot-tokens/*.enc   root@VPS:/opt/gmail-guard/secrets/bot-tokens/
rm -rf out/                        # 🧹 IMPORTANT: delete on the laptop!

# back on the VPS: only the container user (10001) may read
sudo chown -R 10001:10001 secrets && sudo chmod -R go-rwx secrets

sudo cp guard.env.example guard.env && sudo nano guard.env   # enter keys
sudo cp bot.env.example   bot.env   && sudo nano bot.env     # bot token, user ID, key
sudo chmod 600 guard.env bot.env
```

---

## 6️⃣ Start

**Option A – MetaMCP runs on the same server:**

```bash
docker network ls | grep -i metamcp         # find the network name
echo "METAMCP_NETWORK=<name>" | sudo tee .env
sudo docker compose up -d --build
sudo docker compose logs -f                 # both should log "startet | Konten: …"
```

**Option B – MetaMCP elsewhere, or no MetaMCP at all:** in `docker-compose.yml`, remove `metamcp` from the gmail-guard `networks` (and the `networks:` block at the bottom) and enable the `ports:` line bound to your **Tailscale IP**. Never `0.0.0.0`!

💡 **Why not via Coolify?** On purpose. If Hermes ever gained access to Coolify or your git host, it could change the code and redeploy. A plain `docker compose` in `/opt` is one less attack surface.

---

## 7️⃣ Connect Hermes

**Way 1 – via MetaMCP (recommended if you use MetaMCP):**

1. **MCP Servers → New:** type **Streamable HTTP**, URL `http://gmail-guard:8000/mcp` (option B: `http://<tailscale-ip>:8765/mcp`), bearer token = your `MCP_BEARER_TOKEN`
2. **Namespace → New:** `gmail` → add **only** gmail-guard
3. **Endpoint → New:** `gmail` → namespace `gmail` → **require API key: ON**
4. **Create an API key** → use it only for Hermes

⚠️ Do **not** add gmail-guard to a namespace that other clients use.

**Way 2 – direct (no MetaMCP):** Hermes talks to gmail-guard directly over Tailscale (option B), using `MCP_BEARER_TOKEN` as bearer token.

> Menu names in MetaMCP may differ slightly between versions.

---

## 8️⃣ Configure Hermes (on every Hermes machine)

1. `~/.hermes/.env` → `METAMCP_GMAIL_KEY=…` (key only, **without** "Bearer")
2. Paste [`hermes/config-snippet.yaml`](../hermes/config-snippet.yaml) into `~/.hermes/config.yaml`
3. Add [`hermes/gmail-rules.md`](../hermes/gmail-rules.md) to Hermes' memory or as a skill
4. Test: `hermes mcp test gmail`

---

## 9️⃣ Security check (on the VPS) 🔐

The **most important step**. The whole lock depends on Hermes not being able to reach the containers.

```bash
id <hermes-user>                 # ❌ must NOT be in "docker" or "sudo"
sudo -l -U <hermes-user>         # ❌ no sudo rights
sudo -u <hermes-user> ls /opt/gmail-guard/secrets     # ✅ must say "Permission denied"
sudo -u <hermes-user> cat /opt/gmail-guard/guard.env  # ✅ must say "Permission denied"
```

- ☐ Hermes runs as its **own user** (not root)
- ☐ Hermes has **no** Coolify API token and **no** write access to this repo
- ☐ `out/` is deleted on the laptop
- ☐ `guard.env` / `bot.env` are **not** in git (see `.gitignore`)

### 🧪 Test plan (5 minutes)

| Test | Ask Hermes to … | Expected |
|---|---|---|
| 1 | "Summarize today's unread mail" | summary ✅ |
| 2 | "Send a mail to test@…" | only a draft + approval request ✅ |
| 3 | Tap **Send** in Telegram | mail goes out ✅ |
| 4 | "Move 30 newsletters to trash" | bulk approval in Telegram ✅ |
| 5 | `/stopp`, then let Hermes read | blocked ✅, then `/weiter` |

---

## 📨 Forwarding mails to Hermes

No separate mailbox needed. Once per account (about 3 minutes):

1. Create two Gmail labels: `An Hermes` and `Hermes erledigt`
2. **Settings → Filters → Create filter:**
   - **From:** `you@example.com` (several: `address1 OR address2`)
   - **To:** `you+hermes@example.com`
   - → **Apply label:** `An Hermes` · **Skip the inbox** (optional)
3. Create a **recurring task** in Hermes, e.g. every 15 minutes:
   > "Process the mails labelled *An Hermes* according to the Gmail rules."

**Usage:** forward to `you+hermes@example.com`, optionally with a note on top:

| Note | What Hermes does |
|---|---|
| *(none)* or `brain` | 🧠 save to your second brain |
| `zusammenfassen` / `summarize` | 📝 short summary via Telegram |
| `aufgabe` / `task` | ✅ create a to-do |
| `erinnern friday` / `remind friday` | ⏰ reminder |

💡 **Even faster on mobile:** just apply the label `An Hermes`.

🔐 The filter checks the **sender**. If a stranger writes to your `+hermes` address, nothing happens.

---

## 🎚️ Raising the level

In `guard.env`: `GUARD_MODE=read` → `organize` → `full`, then `sudo docker compose up -d`.

## 🚦 Bulk brake (in `guard.env`)

| Setting | Default | Meaning |
|---|---|---|
| `BRAKE_TRASH` | 20 | more than 20 mails per hour to trash → Telegram asks |
| `BRAKE_SPAM` | 20 | same for spam |
| `BRAKE_ARCHIVE` | 50 | archiving is harmless, so more generous |
| `DAILY_TRASH_LIMIT` | 100 | more than 100 per day → Telegram always asks |

The brake counts **per hour**, not per call. Many small batches don't get around it.

## 📱 Telegram commands

| Command | Effect |
|---|---|
| `/status` | open requests + accounts |
| `/heute` | what Hermes did today |
| `/stopp` | 🛑 **KILL SWITCH**: Hermes can't do anything |
| `/weiter` | lift the kill switch |

A daily report arrives automatically at 8 pm (`SUMMARY_HOUR`).

## 🆘 Troubleshooting

| Problem | Fix |
|---|---|
| Access expires after 7 days | Google app still in testing → set "In production", reconnect the account |
| "No refresh token" | [myaccount.google.com/permissions](https://myaccount.google.com/permissions) → remove the app → reconnect |
| Bot doesn't message you | Pressed `/start` in the bot? User ID correct? |
| MetaMCP can't reach gmail-guard | check the network name in `.env`: `docker network inspect <name>` |
| New account not visible | `sudo docker compose restart` |
