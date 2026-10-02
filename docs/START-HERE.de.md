# 🚀 Gmail Guard – Einfach starten

[🇬🇧 English](START-HERE.md) · **🇩🇪 Deutsch** · [← zurück zur README](../README.de.md)

**Ziel:** Hermes verwaltet dein **ganzes Gmail-Postfach**, und du behältst die Kontrolle.

## 🎯 Was du am Ende hast

- 🏷️ Hermes legt **Labels** an und **sortiert** deine Mails
- 🚫 Hermes sortiert **Spam** und Newsletter aus
- 👀 Hermes schaut, **was reinkommt**, und schreibt dir **Antwort-Entwürfe**
- 🔗 Hermes schickt dir den **Link direkt zum Entwurf in Gmail**
- ✅ **Senden tust nur du**, in Gmail selbst

⏱️ **Dauer:** ca. 40 Minuten beim ersten Mal. Du brauchst **kein Python, kein Terminal auf deinem Rechner**, nur einen Browser und Coolify.

---

## 🧭 So ist es aufgebaut

```
Hermes (bleibt, wo er ist) ──► MetaMCP ──► Gmail Guard (dein Server, Coolify) ──► Gmail
                                              └─ hier liegt der Google-Schlüssel
```

**Der Schlüssel liegt auf dem Server, nie bei Hermes.** Deshalb kann eine präparierte Mail Hermes nicht dazu bringen, den Schlüssel zu klauen. Mehr dazu: [README → Sicherheitsmodell](../README.de.md#️-sicherheitsmodell).

> ⛔ **Wichtigste Regel:** Hermes darf **keinen Zugang zu Coolify** haben (kein API-Token, kein Login, keine SSH-Schlüssel zum Server). Sonst könnte er den Code ändern und neu ausrollen, und die ganze Sperre wäre wertlos.

## 🧰 Das brauchst du

- [ ] Ein Google-Konto (das Gmail, das Hermes verwalten soll)
- [ ] Coolify auf einem Server (und MetaMCP dort, wenn du es nutzt)
- [ ] Einen Browser

---

## 1️⃣ Google vorbereiten ⏱️ 15 Min · 🌐 Browser

Das ist der längste Teil. Danach wird es leicht.

1. Öffne [console.cloud.google.com](https://console.cloud.google.com)
2. Projekt-Auswahl oben → **Neues Projekt** → Name `hermes-gmail` → **Erstellen**
3. Suchleiste: **Gmail API** → **Aktivieren**
4. Suchleiste: **Google Auth Platform** → **Los geht's**
   - App-Name `Hermes Gmail`, Support-E-Mail: deine
   - Zielgruppe: **Extern** (Firmenkonto mit Workspace: **Intern**)
   - Kontakt-E-Mail: deine → fertigstellen
5. Links **Zielgruppe** → bei **Testnutzer** → **Add users** → **deine Gmail-Adresse** eintragen → Speichern
   - ⚠️ Im Testmodus läuft der Zugang nach **7 Tagen** ab. Dann einmal Phase 3 wiederholen (2 Minuten).
   - *Dauerhaft ohne Ablauf:* Links **Branding** ausfüllen (Startseite, Datenschutz-Link, Domain) → **Zielgruppe → App veröffentlichen**. Geht auch später.
6. Links **Clients** → **Client erstellen** → Typ **Desktop-App** → **Erstellen**
7. Notiere dir **Client-ID** und **Clientschlüssel** (stehen auf der Seite, oder in der heruntergeladenen JSON unter `client_id` und `client_secret`)

✅ **Fertig, wenn:** du **Client-ID** und **Clientschlüssel** hast.

> 💡 Beim Login später kommt „Google hat diese App nicht überprüft“. Das ist **deine eigene App**. → **Erweitert** → **Weiter**.

---

## 2️⃣ In Coolify starten ⏱️ 10 Min · 🖥️ Coolify

1. **Projekt → + New Resource →** Public Repository
2. URL: `https://github.com/oliverhees/hermes-gmail-guard`
3. **Build Pack: Docker Compose** · **Compose-Datei:** `/docker-compose.coolify.yml`
4. **Environment Variables** → diese drei eintragen:

| Name | Wert |
|---|---|
| `GOOGLE_CLIENT_ID` | die Client-ID aus Phase 1 |
| `GOOGLE_CLIENT_SECRET` | der Clientschlüssel aus Phase 1 |
| `GUARD_MODE` | `full` (Postfach verwalten + Entwürfe) |

5. **Keine Domain** vergeben ❌ (Gmail Guard darf nicht aus dem Internet erreichbar sein)
6. **Deploy**

✅ **Fertig, wenn:** in den Logs **„gmail-guard startet | Modus: full | Konten: KEINE“** steht. („KEINE“ ist richtig, das Konto kommt jetzt.)

> 💡 Den Schlüssel zum Verschlüsseln und das Zugangs-Passwort für MetaMCP erzeugt der Server beim ersten Start selbst und merkt sie sich in seinem Speicher (Volume `guard-data`). Du musst nichts erzeugen oder einfügen.

---

## 3️⃣ Gmail-Konto verbinden ⏱️ 3 Min · 🖥️ Coolify-Terminal + 🌐 Browser

1. In Coolify: Resource → Dienst **gmail-guard** → **Terminal**
   *(Alternativ auf dem Server: `docker ps`, dann `docker exec -it <Name von gmail-guard> sh`)*
2. Tippe ein:
   ```
   python -m app.connect
   ```
3. Kurzname: Enter (`privat`)
4. Es erscheint ein **Link**. Öffne ihn in deinem Browser und melde dich mit dem **Testnutzer-Konto** an. Klicke auf **Erweitert → Weiter → Erlauben**.
5. Danach zeigt der Browser eine **Fehlerseite** („Seite nicht erreichbar“). **Das ist richtig.**
6. Kopiere die **komplette Adresse** aus der Browserzeile (beginnt mit `http://localhost:8080/?state=…`) und füge sie im Terminal ein. Enter.

✅ **Fertig, wenn:** „✅ Hermes darf jetzt …@gmail.com verwalten“ erscheint. Ein Neustart ist nicht nötig.

---

## 4️⃣ Mit MetaMCP verbinden ⏱️ 5 Min · 🖥️ MetaMCP

1. Im Coolify-Terminal von gmail-guard:
   ```
   python -m app.connect --show
   ```
   → kopiere das **MetaMCP-Bearer-Token**
2. **Guard und MetaMCP müssen im gleichen Docker-Netz sein.** Dafür tritt der Guard dem Netz von MetaMCP bei (MetaMCP selbst bleibt unangetastet):

   **⚡ Schnellweg, nur Kopieren und Einfügen** (auf dem Server, als Terminal-Befehl):
   ```
   curl -fsSL https://raw.githubusercontent.com/oliverhees/hermes-gmail-guard/main/scripts/connect-metamcp.sh | bash
   ```
   Das Skript findet Guard, MetaMCP und das Netz selbst, hängt den Guard ein und testet die Leitung (Erwartung: `status 401`). MetaMCP bleibt unangetastet.
   Wer nichts aus dem Netz ausführen will: Inhalt von [`scripts/connect-metamcp.sh`](../scripts/connect-metamcp.sh) öffnen, lesen und einfügen.
   Danach in MetaMCP **Reconnect** klicken.
   ⚠️ Das hält nur bis zum nächsten Deploy des Guards. Dauerhaft ist die Variable `METAMCP_NETWORK` (nächster Schritt).

   **Dauerhaft** (von Hand):
   - Auf dem Server den Netznamen von MetaMCP herausfinden:
     ```
     docker ps --format '{{.Names}}' | grep -i app-      # MetaMCP-Container suchen
     docker inspect <MetaMCP-Container> --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}'
     ```
   - In Coolify beim Guard unter **Environment Variables** eintragen: `METAMCP_NETWORK=<dieser Netzname>`
   - Guard **neu deployen**
   - ⚠️ MetaMCP selbst **nicht** mit „Connect to Predefined Network“ ins Netz `coolify` hängen. Bei einem Test konnte man sich danach nicht mehr in MetaMCP einloggen.
3. **MCP Servers → Neu:** Typ **Streamable HTTP** · URL `http://gmail-guard:8000/mcp` · Bearer-Token von oben
4. **Namespace → Neu:** `gmail` → **nur** gmail-guard hinzufügen
5. **Endpoint → Neu:** `gmail` → Namespace `gmail` → **API-Key-Pflicht AN**
6. **API-Key erzeugen**

✅ **Fertig, wenn:** MetaMCP die Gmail-Werkzeuge anzeigt.

> Menünamen in Coolify und MetaMCP können je nach Version abweichen.

---

## 5️⃣ Hermes verbinden ⏱️ 3 Min · 💻 dort, wo Hermes läuft

1. `~/.hermes/.env` → `METAMCP_GMAIL_KEY=<dein API-Key>` (ohne „Bearer“)
2. [`hermes/config-snippet.yaml`](../hermes/config-snippet.yaml) in `~/.hermes/config.yaml` einfügen (URL anpassen)
3. Test: `hermes mcp test gmail`

✅ **Fertig, wenn:** der Test deine Gmail-Werkzeuge zeigt.

---

## 6️⃣ Testen ⏱️ 5 Min · 💬 Hermes

| # | Sag Hermes … | Erwartung |
|---|---|---|
| 1 | „Fass meine ungelesenen Mails von heute zusammen“ | Zusammenfassung ✅ |
| 2 | „Leg einen Entwurf an mich selbst an, Betreff: Test“ | Entwurf **+ Link** zu Gmail ✅ |
| 3 | Den Link öffnen und im Gmail-Entwurf **selbst senden** | Mail geht raus ✅ |
| 4 | „Leg 30 Newsletter in den Papierkorb“ | Hermes wird **gebremst** (Masse-Bremse) ✅ |

---

## 7️⃣ Hermes zum Postfach-Verwalter machen ⏱️ 5 Min · 💬 Hermes

1. Lege **beide** in Hermes' Gedächtnis oder als Skill ab:
   - [`hermes/hermes-prompt.de.md`](../hermes/hermes-prompt.de.md): erklärt Hermes die Regeln und alle 16 Werkzeuge (nur dieser MCP, kein Senden, nur Entwürfe)
   - [`hermes/gmail-rules.de.md`](../hermes/gmail-rules.de.md): die wiederkehrende Sortier-Aufgabe
2. Sag Hermes **einmal**:

> „Richte die Labels aus dem Abschnitt *Postfach-Verwalter* in meinem Konto `privat` ein. Sortiere dann die Mails der letzten 3 Tage. Lösche nichts.“

3. Dann **eine wiederkehrende Aufgabe**, z.B. alle 20 Minuten:

> „Arbeite mein Postfach `privat` nach dem Abschnitt *Postfach-Verwalter* in den Gmail-Regeln ab.“

✅ **Fertig!** Ab jetzt meldet sich Hermes bei dir, wenn etwas Neues da ist, mit Links zu den Entwürfen.

---

## 📱 Alltag in 10 Sekunden

| Du willst … | Dann … |
|---|---|
| Entwurf prüfen und senden | Link von Hermes öffnen → prüfen → in Gmail **Senden** |
| Entwurf ändern | im Gmail-Entwurf ändern, dann selbst senden |
| Alles sofort stoppen | Gmail Guard in Coolify **stoppen** |

**Masse-Bremse:** Räumt Hermes mehr als 20 Mails pro Stunde in Papierkorb/Spam, lehnt Gmail Guard ab und Hermes sagt dir Bescheid. Beim **ersten Aufräumen** eines großen Postfachs darum in Etappen (stündlich) arbeiten.

---

## 🆘 Probleme

| Problem | Lösung |
|---|---|
| Zugang läuft nach 7 Tagen ab | Testmodus (siehe Phase 1, Schritt 5). `python -m app.connect` nochmal ausführen, gleicher Kurzname ersetzt den alten Zugang |
| „GOOGLE_CLIENT_ID … fehlen“ | In Coolify die zwei Werte eintragen und neu deployen |
| „Kein Refresh-Token“ | [myaccount.google.com/permissions](https://myaccount.google.com/permissions) → App entfernen → nochmal verbinden |
| Browser zeigt nach dem Erlauben `Zugriff blockiert` | Ist deine Adresse unter **Testnutzer** eingetragen? (Phase 1, Schritt 5) |
| Das Coolify-Terminal geht nicht | Auf dem Server `docker exec -it <Name> sh` benutzen (siehe Phase 3) |
| MetaMCP: „Connection Error“ (auch nach einem Neu-Deploy) | **Einfügen und fertig:** `curl -fsSL https://raw.githubusercontent.com/oliverhees/hermes-gmail-guard/main/scripts/connect-metamcp.sh \| bash`, dann in MetaMCP **Reconnect**. Ursache: Guard und MetaMCP nicht im selben Netz (Phase 4, Schritt 2). Test: `docker exec <MetaMCP-Container> node -e "fetch('http://gmail-guard:8000/mcp',{method:'POST'}).then(r=>console.log(r.status))"` muss `401` zeigen |
| Deploy: „network … not found“ | `METAMCP_NETWORK` falsch geschrieben. Netznamen prüfen mit `docker network ls` |
| Zweites Konto | `python -m app.connect --name firma` |

---

## ➕ Optional

- **Senden per Tipp in Telegram** (zusätzlicher Bot, Masse-Freigabe in Telegram): Anleitung in [SETUP.de.md](SETUP.de.md), Compose-Datei `docker-compose.coolify.bot.yml`, Einrichtung mit `python start.py` (Mac/Linux: `python3 start.py`).
- **Alle Einstellungen, Sicherheits-Check, Mails gezielt an Hermes weiterleiten:** [SETUP.de.md](SETUP.de.md)
