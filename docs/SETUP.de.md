# 🛡️ Gmail Guard – Komplette Anleitung

[🇬🇧 English](SETUP.md) · **🇩🇪 Deutsch** · [← zurück zur README](../README.de.md)

⏱️ **Dauer:** ca. 60–90 Minuten beim ersten Konto, danach ca. 5 Minuten pro weiterem Konto.

---

## 📋 Übersicht: 9 Schritte

| # | Schritt | Wo | ✔ |
|---|---|---|---|
| 1 | Schlüssel erzeugen | Laptop | ☐ |
| 2 | Google Cloud einrichten | Browser | ☐ |
| 3 | Telegram-Freigabe-Bot anlegen | Telegram | ☐ |
| 4 | Konto verbinden | Laptop | ☐ |
| 5 | Auf den Server bringen | VPS | ☐ |
| 6 | Starten | VPS | ☐ |
| 7 | Mit Hermes verbinden (MetaMCP oder direkt) | VPS | ☐ |
| 8 | Hermes einrichten | alle Hermes-Rechner | ☐ |
| 9 | Sicherheits-Check + Tests | VPS | ☐ |

---

## 1️⃣ Schlüssel erzeugen

```bash
pip install -r scripts/requirements.txt
python scripts/gen_secrets.py
```

➡️ Die Ausgabe gehört **in deinen Passwortmanager**:
- `GUARD_TOKEN_KEY` + `MCP_BEARER_TOKEN` → für den gmail-guard
- `BOT_TOKEN_KEY` → für den Freigabe-Bot

Zwei verschiedene Schlüssel sind Absicht: Ein Leck öffnet nie beide Tresore.

---

## 2️⃣ Google Cloud einrichten

> Einmal pro **Konto-Art**: ein Projekt für private Gmail-Konten, eins pro Workspace-Domain.

1. [console.cloud.google.com](https://console.cloud.google.com) → **Neues Projekt**, z.B. `hermes-gmail-privat`
2. **APIs & Dienste → Bibliothek →** „Gmail API“ → **Aktivieren**
3. **OAuth-Zustimmungsbildschirm** (teils auch „Google Auth Platform“ genannt):

| | 🏠 Privates @gmail.com | 🏢 Workspace |
|---|---|---|
| Nutzertyp | **Extern** | **Intern** |
| Danach | **App veröffentlichen → „In Produktion“** ⚠️ | fertig |
| Warum | Im Testmodus läuft der Zugang **alle 7 Tage ab** | Intern = kein Ablauf |
| Beim Login | Warnung „nicht verifiziert“ → *Erweitert → Weiter* | keine Warnung |

4. **Anmeldedaten → OAuth-Client-ID →** Typ **Desktop-App** → JSON herunterladen, z.B. als `client_secret_privat.json`

💡 **Workspace:** Wird der Login blockiert, in der Admin-Konsole unter *Sicherheit → API-Steuerung* prüfen, ob die App erlaubt ist.

---

## 3️⃣ Telegram-Freigabe-Bot anlegen

⚠️ **Ein NEUER Bot, nicht der von Hermes!** Sonst könnte Hermes die Freigabe-Nachrichten mitlesen.

1. In Telegram `@BotFather` → `/newbot` → **Token kopieren**
2. `@userinfobot` anschreiben → deine **User-ID** (eine Zahl) kopieren
3. Deinen neuen Bot öffnen und **`/start` drücken**. Ohne diesen Schritt kann er dir nicht schreiben.

---

## 4️⃣ Konto verbinden (auf dem Laptop, braucht einen Browser)

```bash
export GUARD_TOKEN_KEY='...'   # aus Schritt 1
export BOT_TOKEN_KEY='...'

python scripts/add_account.py --name privat --client-secret client_secret_privat.json --mode full
```

- Es öffnen sich **zwei Logins** nacheinander: einer für den gmail-guard, einer für den Freigabe-Bot.
- Beide Male **dasselbe Konto** wählen.
- Weitere Konten: gleicher Befehl, anderer `--name` (z.B. `firma`).

| `--mode` | gmail-guard darf | Sperre |
|---|---|---|
| `read` | nur lesen | 🔒 Google selbst verhindert alles andere |
| `organize` | + aufräumen | Code-Sperre |
| `full` | + Entwürfe, zusätzlich Bot-Token zum Senden | Code-Sperre |

💡 **Extra-vorsichtig starten?** Erst mit `--mode read` verbinden, später für `full` neu verbinden.

---

## 5️⃣ Auf den Server bringen

```bash
# auf dem VPS
sudo mkdir -p /opt/gmail-guard && cd /opt/gmail-guard
sudo git clone https://github.com/oliverhees/hermes-gmail-guard.git .
sudo mkdir -p secrets/guard-tokens secrets/bot-tokens

# vom Laptop aus
scp out/guard-tokens/*.enc root@VPS:/opt/gmail-guard/secrets/guard-tokens/
scp out/bot-tokens/*.enc   root@VPS:/opt/gmail-guard/secrets/bot-tokens/
rm -rf out/                        # 🧹 WICHTIG: auf dem Laptop löschen!

# wieder auf dem VPS: nur der Container-Benutzer (10001) darf lesen
sudo chown -R 10001:10001 secrets && sudo chmod -R go-rwx secrets

sudo cp guard.env.example guard.env && sudo nano guard.env   # Schlüssel eintragen
sudo cp bot.env.example   bot.env   && sudo nano bot.env     # Bot-Token, User-ID, Schlüssel
sudo chmod 600 guard.env bot.env
```

---

## 6️⃣ Starten

**Variante A – MetaMCP läuft auf demselben Server:**

```bash
docker network ls | grep -i metamcp         # Netzname herausfinden
echo "METAMCP_NETWORK=<name>" | sudo tee .env
sudo docker compose up -d --build
sudo docker compose logs -f                 # beide zeigen "startet | Konten: …"
```

**Variante B – MetaMCP woanders oder gar kein MetaMCP:** In `docker-compose.yml` beim gmail-guard den Eintrag `metamcp` bei `networks` entfernen (und den `networks:`-Block unten) und die `ports:`-Zeile mit deiner **Tailscale-IP** aktivieren. Niemals `0.0.0.0`!

💡 **Warum nicht über Coolify?** Absichtlich. Hätte Hermes irgendwann Zugriff auf Coolify oder dein Git, könnte er Code ändern und neu ausrollen. Ein schlichtes `docker compose` unter `/opt` bietet eine Angriffsfläche weniger.

---

## 7️⃣ Mit Hermes verbinden

**Weg 1 – über MetaMCP (empfohlen, wenn du MetaMCP hast):**

1. **MCP Servers → Neu:** Typ **Streamable HTTP**, URL `http://gmail-guard:8000/mcp` (Variante B: `http://<tailscale-ip>:8765/mcp`), Bearer-Token = dein `MCP_BEARER_TOKEN`
2. **Namespace → Neu:** `gmail` → **nur** den gmail-guard hinzufügen
3. **Endpoint → Neu:** `gmail` → Namespace `gmail` → **API-Key-Pflicht AN**
4. **API-Key erzeugen** → nur für Hermes verwenden

⚠️ Den gmail-guard **nicht** in einen Namespace hängen, den auch andere Clients nutzen.

**Weg 2 – direkt (ohne MetaMCP):** Hermes spricht den gmail-guard direkt über Tailscale an (Variante B), mit `MCP_BEARER_TOKEN` als Bearer-Token.

> Die Menünamen in MetaMCP können je nach Version leicht abweichen.

---

## 8️⃣ Hermes einrichten (auf jedem Hermes-Rechner)

1. `~/.hermes/.env` → `METAMCP_GMAIL_KEY=…` (nur der Key, **ohne** „Bearer“)
2. Inhalt von [`hermes/config-snippet.yaml`](../hermes/config-snippet.yaml) in `~/.hermes/config.yaml` einfügen
3. [`hermes/gmail-rules.de.md`](../hermes/gmail-rules.de.md) in Hermes' Gedächtnis bzw. als Skill ablegen
4. Test: `hermes mcp test gmail`

---

## 9️⃣ Sicherheits-Check (auf dem VPS) 🔐

Der **wichtigste Schritt**. Die ganze Sperre hängt daran, dass Hermes nicht an die Container kommt.

```bash
id <hermes-benutzer>             # ❌ darf NICHT in "docker" oder "sudo" stehen
sudo -l -U <hermes-benutzer>     # ❌ keine sudo-Rechte
sudo -u <hermes-benutzer> ls /opt/gmail-guard/secrets    # ✅ muss "Permission denied" sein
sudo -u <hermes-benutzer> cat /opt/gmail-guard/guard.env # ✅ muss "Permission denied" sein
```

- ☐ Hermes läuft als **eigener Benutzer** (nicht root)
- ☐ Hermes hat **keinen** Coolify-API-Token und **keine** Schreibrechte auf dieses Repo
- ☐ Auf dem Laptop ist `out/` gelöscht
- ☐ `guard.env` / `bot.env` stehen **nicht** in Git (siehe `.gitignore`)

### 🧪 Testplan (5 Minuten)

| Test | Hermes soll … | Erwartung |
|---|---|---|
| 1 | „Fass meine ungelesenen Mails von heute zusammen“ | Zusammenfassung ✅ |
| 2 | „Schick eine Mail an test@…“ | nur Entwurf + Freigabe-Anfrage ✅ |
| 3 | In Telegram **Senden** drücken | Mail geht raus ✅ |
| 4 | „Leg 30 Newsletter in den Papierkorb“ | Masse-Freigabe in Telegram ✅ |
| 5 | `/stopp`, dann Hermes etwas lesen lassen | blockiert ✅, danach `/weiter` |

---

## 📨 Mails an Hermes weiterleiten

Kein eigenes Postfach nötig. Einmalig pro Konto (ca. 3 Minuten):

1. In Gmail zwei Labels anlegen: `An Hermes` und `Hermes erledigt`
2. **Einstellungen → Filter → Neuer Filter:**
   - **Von:** `deine@adresse.de` (bei mehreren: `adresse1 OR adresse2`)
   - **An:** `deine+hermes@adresse.de`
   - → **Label anwenden:** `An Hermes` · **Posteingang überspringen** (optional)
3. In Hermes eine **wiederkehrende Aufgabe** anlegen, z.B. alle 15 Minuten:
   > „Arbeite die Mails mit Label *An Hermes* nach den Gmail-Regeln ab.“

**Benutzen:** An `deine+hermes@adresse.de` weiterleiten, optional mit einer Notiz oben:

| Notiz | Was Hermes macht |
|---|---|
| *(keine)* oder `brain` | 🧠 ins Second Brain |
| `zusammenfassen` | 📝 Kurzfassung per Telegram |
| `aufgabe` | ✅ To-do anlegen |
| `erinnern freitag` | ⏰ Erinnerung |

💡 **Am Handy noch schneller:** Einfach das Label `An Hermes` setzen.

🔐 Der Filter prüft den **Absender**. Schreibt ein Fremder an deine `+hermes`-Adresse, passiert nichts.

---

## 🎚️ Stufen hochdrehen

In `guard.env`: `GUARD_MODE=read` → `organize` → `full`, dann `sudo docker compose up -d`.

## 🚦 Masse-Bremse (in `guard.env`)

| Einstellung | Standard | Bedeutung |
|---|---|---|
| `BRAKE_TRASH` | 20 | mehr als 20 Mails pro Stunde in den Papierkorb → Telegram fragt |
| `BRAKE_SPAM` | 20 | dasselbe für Spam |
| `BRAKE_ARCHIVE` | 50 | Archivieren ist harmlos, daher großzügiger |
| `DAILY_TRASH_LIMIT` | 100 | mehr als 100 pro Tag → Telegram fragt immer |

Die Bremse zählt **pro Stunde**, nicht pro Aufruf. Viele kleine Portionen umgehen sie nicht.

## 📱 Telegram-Befehle

| Befehl | Wirkung |
|---|---|
| `/status` | offene Anfragen + Konten |
| `/heute` | was Hermes heute getan hat |
| `/stopp` | 🛑 **NOT-AUS**: Hermes kann gar nichts mehr |
| `/weiter` | Not-Aus aufheben |

Jeden Abend um 20 Uhr kommt automatisch ein Tagesbericht.

## 🆘 Probleme

| Problem | Lösung |
|---|---|
| Zugang läuft nach 7 Tagen ab | Google-App steht noch im Testmodus → „In Produktion“ stellen, Konto neu verbinden |
| „Kein Refresh-Token“ | [myaccount.google.com/permissions](https://myaccount.google.com/permissions) → App entfernen → neu verbinden |
| Bot schreibt nicht | `/start` beim Bot gedrückt? User-ID korrekt? |
| MetaMCP erreicht gmail-guard nicht | Netzname in `.env` prüfen: `docker network inspect <name>` |
| Neues Konto nicht sichtbar | `sudo docker compose restart` |
