# 🚀 Gmail Guard – Einfach starten

[🇬🇧 English](START-HERE.md) · **🇩🇪 Deutsch** · [← zurück zur README](../README.de.md)

**Ziel:** Hermes verwaltet dein **ganzes Gmail-Postfach** – und du behältst die Kontrolle.

---

## 🎯 Was du am Ende hast

- 🏷️ Hermes legt **Labels** an und **sortiert** deine Mails
- 🚫 Hermes sortiert **Spam** und Newsletter aus
- 👀 Hermes schaut, **was reinkommt**, und schreibt dir **Antwort-Entwürfe**
- 📱 Du bekommst eine Telegram-Nachricht mit **Link direkt zum Entwurf in Gmail**
- ✅ **Senden tust nur du** – per Tipp in Telegram oder in Gmail selbst

⏱️ **Dauer:** ca. 45 Minuten beim ersten Mal. Weiteres Konto: 5 Minuten.

---

## 🧭 Schritt 0: Wo soll es laufen? (10 Sekunden)

Gmail Guard besteht aus **zwei kleinen Programmen** (Docker). Sie müssen **laufen**, damit Hermes an dein Gmail kommt und die Telegram-Knöpfe funktionieren.

| | 🅰️ **Server mit Coolify** | 🅱️ **Dieser Rechner** |
|---|---|---|
| Läuft auch, wenn dein PC aus ist | ✅ ja | ❌ nein (PC aus = Hermes kommt nicht an Gmail) |
| Aufwand | etwas mehr | am wenigsten |
| Sicherheit | ✅ am besten (Hermes kommt nicht an den Schlüssel) | ⚠️ schwächer, wenn Hermes auf demselben Rechner läuft |
| Passt für | **dauerhaft** | **zum Ausprobieren** |

> 💡 **Hermes selbst darf immer lokal bleiben.** Nur Gmail Guard läuft auf dem Server.
> Nichts geht kaputt, wenn der Rechner aus ist – es passiert dann einfach nichts.

➡️ **Weg 🅰️ (empfohlen):** Phasen 1 → 2 → 3 → **4A** → **5A** → 6 → 7
➡️ **Weg 🅱️:** Phasen 1 → 2 → 3 → **4B** → **5B** → 6 → 7

---

## 🧰 Das brauchst du

- [ ] Ein Google-Konto (das Gmail, das Hermes verwalten soll)
- [ ] Telegram auf dem Handy
- [ ] **Python 3.10+** auf deinem Rechner ([python.org](https://www.python.org/downloads/))
- [ ] 🅰️ Coolify + MetaMCP **oder** 🅱️ [Docker Desktop](https://www.docker.com/products/docker-desktop/)

---

## 1️⃣ Google vorbereiten ⏱️ 15 Min · 🌐 Browser

Das ist der längste Teil. Danach wird es leicht.

1. Öffne [console.cloud.google.com](https://console.cloud.google.com)
2. Oben auf die Projekt-Auswahl → **Neues Projekt** → Name: `hermes-gmail` → **Erstellen**
3. Suchleiste oben: **Gmail API** → **Aktivieren**
4. Suchleiste: **Google Auth Platform** → **Los geht's**
   - App-Name: `Hermes Gmail` · Support-E-Mail: deine
   - Zielgruppe: **Extern** (Workspace-Firmenkonto: **Intern**)
   - Kontakt-E-Mail: deine → fertigstellen
5. Links **Branding** → ausfüllen und **Speichern**:
   - Anwendungs-Startseite: deine Webseite (z.B. `https://aiianer.de`)
   - Datenschutzerklärung: Link auf die Datenschutz-Seite dieser Webseite
   - Autorisierte Domain: die Domain davon (z.B. `aiianer.de`)
   - Ohne diese Angaben bleibt „App veröffentlichen“ **ausgegraut**.
6. Links **Zielgruppe** → **App veröffentlichen** → bestätigen („In Produktion“)
   - ⚠️ **Nicht überspringen!** Sonst läuft der Zugang nach 7 Tagen ab.
   - (Nur bei „Intern“ nicht nötig.)
7. Links **Clients** → **Client erstellen** → Typ **Desktop-App** → **Erstellen**
8. **JSON herunterladen**

**📦 Die Datei kommt in den Projektordner** (Name beginnt mit `client_secret`).

✅ **Fertig, wenn:** eine `client_secret_….json` im Ordner liegt.

> 💡 Beim Login später kommt „Google hat diese App nicht überprüft“. Das ist **deine eigene App**. → **Erweitert** → **Weiter**.

---

## 2️⃣ Telegram-Bot anlegen ⏱️ 3 Min · 📱 Telegram

⚠️ Ein **neuer** Bot. **Nicht** der, den Hermes benutzt.

1. Telegram → **@BotFather** → `/newbot` → Namen vergeben → **Token kopieren**
2. Telegram → **@userinfobot** → schreibt dir deine **User-ID** (Zahl) → **kopieren**
3. Öffne **deinen neuen Bot** und drücke **Start**

✅ **Fertig, wenn:** du Token + User-ID hast und im neuen Bot „Start“ gedrückt hast.

---

## 3️⃣ Setup-Assistent ⏱️ 5 Min · 💻 dein Rechner

```bash
git clone https://github.com/oliverhees/hermes-gmail-guard.git
cd hermes-gmail-guard
python start.py
```

> 🪟🍎🐧 **Gleicher Befehl auf Windows, Mac und Linux.** Unter Mac/Linux heißt er meist `python3 start.py`.
> Beim ersten Mal legt er selbst eine Python-Umgebung an (ca. 1 Minute). Im System wird nichts verändert.

Der Assistent **fragt dich alles** und erzeugt alle Schlüssel selbst:

| Frage | Antwort |
|---|---|
| Wo soll es laufen? | `1` = Server · `2` = dieser Rechner |
| Kurzname | z.B. `privat` |
| Pfad zur `client_secret…json` | Enter (er findet sie selbst) |
| Was darf Hermes? | `3` = ganzes Postfach verwalten |
| Telegram-Token + User-ID | aus Phase 2 |

Dann öffnen sich **2 Browser-Fenster** (Google-Login). **Beide Male dasselbe Konto.**

✅ **Fertig, wenn:** „🎉 Fertig!“ im Terminal steht.

> 🛡️ **Vorsichtig starten?** Wähle `2` (lesen + aufräumen, noch keine Entwürfe). Später den Assistenten nochmal starten und `3` wählen.

---

## 4️⃣ A – Auf den Server mit Coolify ⏱️ 10 Min · 🖥️ Coolify

1. **Coolify → Projekt → + New Resource →** Public Repository (oder Private mit GitHub-App)
2. URL: `https://github.com/oliverhees/hermes-gmail-guard`
3. **Build Pack: Docker Compose** · **Compose-Datei:** `/docker-compose.coolify.yml`
4. **Environment Variables → Developer view**
5. Datei **`out/settings.env`** öffnen → **alles kopieren** → einfügen → **Save**
6. **Keine Domain** vergeben ❌ (Gmail Guard darf nicht aus dem Internet erreichbar sein)
7. **Deploy**

✅ **Fertig, wenn:** in den Logs bei beiden Diensten **„startet | Konten: privat“** steht.

🔐 **Danach:** `out/settings.env` im **Passwortmanager** ablegen und vom Rechner löschen. Du brauchst sie nur, wenn du später ein Konto hinzufügst.

> ⛔ **Wichtigste Sicherheitsregel bei Coolify:**
> Hermes darf **keinen Zugang zu Coolify** haben (kein API-Token, kein Login, keine SSH-Schlüssel zum Server).
> Sonst könnte Hermes den Code ändern und neu ausrollen – dann hilft die ganze Sperre nichts.

---

## 4️⃣ B – Auf diesem Rechner ⏱️ 5 Min · 💻 dein Rechner

1. Docker Desktop **starten**
2. Im Projektordner:

```bash
docker compose -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.local.yml logs
```

✅ **Fertig, wenn:** bei beiden **„startet | Konten: privat“** steht.

> ⚠️ **Ehrlich:** `guard.env` liegt auf deinem Rechner. Kann Hermes dort Dateien lesen, kann er den Schlüssel finden. Für den Dauerbetrieb ist der Server sicherer.

---

## 5️⃣ A – Mit MetaMCP verbinden ⏱️ 5 Min · 🖥️ MetaMCP

1. MetaMCP muss im **gleichen Docker-Netz** sein: In Coolify bei **MetaMCP** → *Advanced* → **Connect to Predefined Network** ✔ → neu starten
2. **MCP Servers → Neu:**
   - Typ: **Streamable HTTP**
   - URL: `http://gmail-guard:8000/mcp`
   - Bearer-Token: `MCP_BEARER_TOKEN` aus `settings.env`
3. **Namespace → Neu:** `gmail` → **nur** gmail-guard hinzufügen
4. **Endpoint → Neu:** `gmail` → Namespace `gmail` → **API-Key-Pflicht AN**
5. **API-Key erzeugen**

Dann **auf deinem Hermes-Rechner:**

1. `~/.hermes/.env` → `METAMCP_GMAIL_KEY=<dein API-Key>` (ohne „Bearer“)
2. [`hermes/config-snippet.yaml`](../hermes/config-snippet.yaml) in `~/.hermes/config.yaml` einfügen (URL anpassen)
3. Test: `hermes mcp test gmail`

✅ **Fertig, wenn:** der Test deine Gmail-Werkzeuge zeigt.

> Die Menünamen in Coolify/MetaMCP können je nach Version abweichen.

---

## 5️⃣ B – Hermes direkt verbinden ⏱️ 2 Min · 💻 dein Rechner

1. `~/.hermes/.env` → `GMAIL_GUARD_KEY=<MCP_BEARER_TOKEN aus guard.env>`
2. [`hermes/config-snippet.local.yaml`](../hermes/config-snippet.local.yaml) in `~/.hermes/config.yaml` einfügen
3. Test: `hermes mcp test gmail`

✅ **Fertig, wenn:** der Test deine Gmail-Werkzeuge zeigt.

---

## 6️⃣ Testen ⏱️ 5 Min · 💬 Hermes + Telegram

| # | Sag Hermes … | Erwartung |
|---|---|---|
| 1 | „Fass meine ungelesenen Mails von heute zusammen“ | Zusammenfassung ✅ |
| 2 | „Leg einen Entwurf an mich selbst an, Betreff: Test“ | Entwurf **+ Link** zu Gmail ✅ |
| 3 | „Frag die Freigabe dafür an“ | Telegram zeigt Vorschau ✅ |
| 4 | In Telegram **Senden** drücken | Mail geht raus ✅ |
| 5 | In Telegram `/stopp`, dann Hermes etwas lesen lassen | blockiert ✅ → `/weiter` |

✅ **Fertig, wenn:** alle 5 Tests passen.

---

## 7️⃣ Hermes zum Postfach-Verwalter machen ⏱️ 5 Min · 💬 Hermes

1. Lege [`hermes/gmail-rules.de.md`](../hermes/gmail-rules.de.md) in Hermes' Gedächtnis oder als Skill ab
2. Sag Hermes **einmal**:

> „Richte die Labels aus dem Abschnitt *Postfach-Verwalter* in meinem Konto `privat` ein. Sortiere dann die Mails der letzten 3 Tage. Lösche nichts.“

3. Dann **eine wiederkehrende Aufgabe**, z.B. alle 20 Minuten:

> „Arbeite mein Postfach `privat` nach dem Abschnitt *Postfach-Verwalter* in den Gmail-Regeln ab.“

✅ **Fertig!** Ab jetzt meldet sich Hermes in Telegram, wenn etwas Neues da ist, mit Links zu den Entwürfen.

---

## 📱 Alltag in 10 Sekunden

| Du willst … | Dann … |
|---|---|
| Entwurf prüfen und senden | In Telegram **✅ Senden** drücken |
| Entwurf selbst ändern | **🔗 Entwurf in Gmail öffnen** → ändern → selbst senden |
| Gmail im Browser öffnen | In Telegram `/gmail` |
| Alles sofort stoppen | `/stopp` (aufheben: `/weiter`) |
| Sehen, was Hermes getan hat | `/heute` (jeden Abend 20 Uhr kommt es automatisch) |

**Masse-Bremse:** Räumt Hermes mehr als 20 Mails pro Stunde in Papierkorb/Spam, fragt Telegram dich erst. Gewollt. Beim **ersten Aufräumen** eines großen Postfachs tippst du also öfter auf „Erlauben“.

---

## 🆘 Probleme

| Problem | Lösung |
|---|---|
| Zugang läuft nach 7 Tagen ab | Google-App steht noch auf „Testing“ → Phase 1, Schritt 5 → Assistenten nochmal starten |
| „Kein Refresh-Token“ | [myaccount.google.com/permissions](https://myaccount.google.com/permissions) → App entfernen → Assistenten nochmal |
| Bot schreibt nichts | Im Bot **Start** gedrückt? User-ID richtig? |
| MetaMCP erreicht gmail-guard nicht | MetaMCP **und** Gmail Guard im selben Netz (Phase 5A, Schritt 1) |
| Coolify: „network coolify not found“ | Auf dem Coolify-Server `docker network ls` – das Netz heißt dort anders? Dann in `docker-compose.coolify.yml` den Namen anpassen |
| Zweites Konto | Assistenten nochmal starten (alte `out/settings.env` wieder in `out/` legen!), dann in Coolify neu einfügen und neu deployen |
| Neues Konto nicht sichtbar (lokal) | `docker compose -f docker-compose.local.yml restart` |

---

## 🔬 Mehr Details?

- Alle Einstellungen, Sicherheits-Check, Mails gezielt an Hermes weiterleiten: [**SETUP.de.md**](SETUP.de.md)
- Wie sicher ist das? [README → Sicherheitsmodell](../README.de.md#️-sicherheitsmodell)
