# 🚀 Gmail Guard – Easy Start

**🇬🇧 English** · [🇩🇪 Deutsch](START-HERE.de.md) · [← back to README](../README.md)

**Goal:** Hermes manages your **whole Gmail mailbox** – and you stay in control.

> ℹ️ The setup assistant, the approval bot and the tool messages are currently in **German**. Bot commands: `/status`, `/heute` (today), `/gmail`, `/stopp` (kill switch), `/weiter` (resume).

---

## 🎯 What you get

- 🏷️ Hermes creates **labels** and **sorts** your mail
- 🚫 Hermes filters out **spam** and newsletters
- 👀 Hermes watches **what comes in** and writes **reply drafts**
- 📱 You get a Telegram message with a **link straight to the draft in Gmail**
- ✅ **Only you send** – with a tap in Telegram or in Gmail itself

⏱️ **Time:** about 45 minutes the first time. Another account: 5 minutes.

---

## 🧭 Step 0: Where should it run? (10 seconds)

Gmail Guard is **two small programs** (Docker). They must be **running** so that Hermes can reach your Gmail and the Telegram buttons work.

| | 🅰️ **Server with Coolify** | 🅱️ **This computer** |
|---|---|---|
| Runs while your PC is off | ✅ yes | ❌ no (PC off = Hermes can't reach Gmail) |
| Effort | a bit more | least |
| Security | ✅ best (Hermes can't reach the key) | ⚠️ weaker if Hermes runs on the same machine |
| Good for | **permanent use** | **trying it out** |

> 💡 **Hermes itself can always stay local.** Only Gmail Guard runs on the server.
> Nothing breaks when the computer is off – nothing just happens.

➡️ **Path 🅰️ (recommended):** phases 1 → 2 → 3 → **4A** → **5A** → 6 → 7
➡️ **Path 🅱️:** phases 1 → 2 → 3 → **4B** → **5B** → 6 → 7

---

## 🧰 What you need

- [ ] A Google account (the Gmail Hermes should manage)
- [ ] Telegram on your phone
- [ ] **Python 3.10+** on your computer ([python.org](https://www.python.org/downloads/))
- [ ] 🅰️ Coolify + MetaMCP **or** 🅱️ [Docker Desktop](https://www.docker.com/products/docker-desktop/)

---

## 1️⃣ Prepare Google ⏱️ 15 min · 🌐 browser

This is the longest part. It gets easy afterwards.

1. Open [console.cloud.google.com](https://console.cloud.google.com)
2. Project picker at the top → **New project** → name: `hermes-gmail` → **Create**
3. Search bar: **Gmail API** → **Enable**
4. Search bar: **Google Auth Platform** → **Get started**
   - App name: `Hermes Gmail` · support email: yours
   - Audience: **External** (Workspace company account: **Internal**)
   - Contact email: yours → finish
5. Left: **Branding** → fill in and **Save**:
   - Application home page: your website (e.g. `https://aiianer.de`)
   - Privacy policy: link to the privacy page of that website
   - Authorized domain: the domain of those links (e.g. `aiianer.de`)
   - Without these, "Publish app" stays **greyed out**.
6. Left: **Audience** → **Publish app** → confirm ("In production")
   - ⚠️ **Don't skip!** Otherwise access expires after 7 days.
   - (Not needed for "Internal".)
7. Left: **Clients** → **Create client** → type **Desktop app** → **Create**
8. **Download JSON**

**📦 Put the file into the project folder** (name starts with `client_secret`).

✅ **Done when:** a `client_secret_….json` is in the folder.

> 💡 At login you will see "Google hasn't verified this app". It is **your own app**. → **Advanced** → **Continue**.

---

## 2️⃣ Create the Telegram bot ⏱️ 3 min · 📱 Telegram

⚠️ A **new** bot. **Not** the one Hermes uses.

1. Telegram → **@BotFather** → `/newbot` → pick a name → **copy the token**
2. Telegram → **@userinfobot** → it tells you your **user ID** (a number) → **copy**
3. Open **your new bot** and press **Start**

✅ **Done when:** you have token + user ID and pressed "Start" in the new bot.

---

## 3️⃣ Setup assistant ⏱️ 5 min · 💻 your computer

```bash
git clone https://github.com/oliverhees/hermes-gmail-guard.git
cd hermes-gmail-guard
python start.py
```

> 🪟🍎🐧 **Same command on Windows, Mac and Linux.** On Mac/Linux it is usually `python3 start.py`.
> The first time it creates its own Python environment (about 1 minute). Nothing is changed on your system.

The assistant **asks you everything** and generates all keys itself:

| Question | Answer |
|---|---|
| Where should it run? | `1` = server · `2` = this computer |
| Short name | e.g. `privat` |
| Path to `client_secret…json` | Enter (it finds it) |
| What may Hermes do? | `3` = manage the whole mailbox |
| Telegram token + user ID | from phase 2 |

Then **2 browser windows** open (Google login). **Both times the same account.**

✅ **Done when:** "🎉 Fertig!" appears in the terminal.

> 🛡️ **Start careful?** Pick `2` (read + clean up, no drafts yet). Later run the assistant again and pick `3`.

---

## 4️⃣ A – On the server with Coolify ⏱️ 10 min · 🖥️ Coolify

1. **Coolify → project → + New Resource →** Public Repository (or Private with the GitHub app)
2. URL: `https://github.com/oliverhees/hermes-gmail-guard`
3. **Build pack: Docker Compose** · **Compose file:** `/docker-compose.coolify.yml`
4. **Environment Variables → Developer view**
5. Open **`out/settings.env`** → **copy everything** → paste → **Save**
6. **Do not assign a domain** ❌ (Gmail Guard must not be reachable from the internet)
7. **Deploy**

✅ **Done when:** both services log **"startet | Konten: privat"**.

🔐 **Afterwards:** store `out/settings.env` in your **password manager** and delete it from the computer. You only need it to add an account later.

> ⛔ **Most important security rule with Coolify:**
> Hermes must have **no access to Coolify** (no API token, no login, no SSH key to the server).
> Otherwise Hermes could change the code and redeploy it – and the whole lock is worthless.

---

## 4️⃣ B – On this computer ⏱️ 5 min · 💻 your computer

1. **Start** Docker Desktop
2. In the project folder:

```bash
docker compose -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.local.yml logs
```

✅ **Done when:** both log **"startet | Konten: privat"**.

> ⚠️ **Honest note:** `guard.env` lives on your computer. If Hermes can read files there, it can find the key. For permanent use the server is safer.

---

## 5️⃣ A – Connect via MetaMCP ⏱️ 5 min · 🖥️ MetaMCP

1. MetaMCP must be in the **same Docker network**: in Coolify on **MetaMCP** → *Advanced* → **Connect to Predefined Network** ✔ → restart
2. **MCP Servers → New:**
   - Type: **Streamable HTTP**
   - URL: `http://gmail-guard:8000/mcp`
   - Bearer token: `MCP_BEARER_TOKEN` from `settings.env`
3. **Namespace → New:** `gmail` → add **only** gmail-guard
4. **Endpoint → New:** `gmail` → namespace `gmail` → **API key required ON**
5. **Create an API key**

Then **on your Hermes machine:**

1. `~/.hermes/.env` → `METAMCP_GMAIL_KEY=<your API key>` (without "Bearer")
2. Paste [`hermes/config-snippet.yaml`](../hermes/config-snippet.yaml) into `~/.hermes/config.yaml` (adjust the URL)
3. Test: `hermes mcp test gmail`

✅ **Done when:** the test lists your Gmail tools.

> Menu names in Coolify/MetaMCP may differ by version.

---

## 5️⃣ B – Connect Hermes directly ⏱️ 2 min · 💻 your computer

1. `~/.hermes/.env` → `GMAIL_GUARD_KEY=<MCP_BEARER_TOKEN from guard.env>`
2. Paste [`hermes/config-snippet.local.yaml`](../hermes/config-snippet.local.yaml) into `~/.hermes/config.yaml`
3. Test: `hermes mcp test gmail`

✅ **Done when:** the test lists your Gmail tools.

---

## 6️⃣ Test it ⏱️ 5 min · 💬 Hermes + Telegram

| # | Tell Hermes … | Expected |
|---|---|---|
| 1 | "Summarize my unread mails from today" | summary ✅ |
| 2 | "Create a draft to myself, subject: Test" | draft **+ link** to Gmail ✅ |
| 3 | "Request approval for it" | Telegram shows the preview ✅ |
| 4 | Press **Senden** (send) in Telegram | mail goes out ✅ |
| 5 | `/stopp` in Telegram, then let Hermes read something | blocked ✅ → `/weiter` |

✅ **Done when:** all 5 tests pass.

---

## 7️⃣ Turn Hermes into your inbox manager ⏱️ 5 min · 💬 Hermes

1. Put [`hermes/gmail-rules.md`](../hermes/gmail-rules.md) into Hermes' memory or a skill
2. Tell Hermes **once**:

> "Set up the labels from the section *Inbox manager* in my account `privat`. Then sort the mails of the last 3 days. Delete nothing."

3. Then **one recurring task**, e.g. every 20 minutes:

> "Work through my mailbox `privat` following the section *Inbox manager* in the Gmail rules."

✅ **Done!** From now on Hermes pings you in Telegram when there is something new, with links to the drafts.

---

## 📱 Everyday use in 10 seconds

| You want to … | Then … |
|---|---|
| Check and send a draft | Press **✅ Senden** in Telegram |
| Edit a draft yourself | **🔗 Entwurf in Gmail öffnen** → edit → send yourself |
| Open Gmail in the browser | `/gmail` in Telegram |
| Stop everything now | `/stopp` (undo: `/weiter`) |
| See what Hermes did | `/heute` (arrives automatically every evening at 8 pm) |

**Bulk brake:** If Hermes moves more than 20 mails per hour to trash/spam, Telegram asks you first. That is intended. On the **first clean-up** of a big mailbox you will tap "Erlauben" (allow) more often.

---

## 🆘 Problems

| Problem | Fix |
|---|---|
| Access expires after 7 days | Google app is still "Testing" → phase 1, step 5 → run the assistant again |
| "Kein Refresh-Token" | [myaccount.google.com/permissions](https://myaccount.google.com/permissions) → remove the app → run the assistant again |
| Bot doesn't write | Pressed **Start** in the bot? User ID correct? |
| MetaMCP can't reach gmail-guard | MetaMCP **and** Gmail Guard in the same network (phase 5A, step 1) |
| Coolify: "network coolify not found" | On the Coolify server run `docker network ls` – is the network named differently? Adjust the name in `docker-compose.coolify.yml` |
| Second account | Run the assistant again (put the old `out/settings.env` back into `out/`!), paste into Coolify again and redeploy |
| New account not visible (local) | `docker compose -f docker-compose.local.yml restart` |

---

## 🔬 More details?

- All settings, security check, forwarding mails to Hermes: [**SETUP.md**](SETUP.md)
- How safe is this? [README → Security model](../README.md#️-security-model)
