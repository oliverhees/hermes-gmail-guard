#!/usr/bin/env bash
# Hängt Gmail Guard ins Docker-Netz von MetaMCP (MetaMCP selbst bleibt unangetastet).
# Auf dem SERVER ausführen. Sicher mehrfach ausführbar.
# Hält nur bis zum nächsten Deploy des Guards. Dauerhaft: Variable METAMCP_NETWORK in Coolify (siehe Ausgabe).
set -u

GUARD=$(docker ps --format '{{.Names}}' | grep '^gmail-guard' | head -1)
META=$(docker ps --format '{{.Names}} {{.Image}}' | grep -i 'metatool-ai/metamcp' | awk '{print $1}' | head -1)

[ -n "$GUARD" ] || { echo "❌ Kein Container 'gmail-guard…' gefunden. Läuft der Guard in Coolify?"; exit 1; }
[ -n "$META" ]  || { echo "❌ Kein MetaMCP-Container gefunden. Läuft MetaMCP auf DIESEM Server?"; exit 1; }

NET=$(docker inspect "$META" --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}{{"\n"}}{{end}}' | grep -v -e '^coolify$' -e '^$' | head -1)
[ -n "$NET" ] || { echo "❌ MetaMCP hängt in keinem eigenen Netz (nur 'coolify'?). Schick mir: docker inspect $META"; exit 1; }

echo "Guard:   $GUARD"
echo "MetaMCP: $META"
echo "Netz:    $NET"

OUT=$(docker network connect --alias gmail-guard "$NET" "$GUARD" 2>&1)
case "$OUT" in
  "")                  echo "✅ Guard ins Netz gehängt." ;;
  *"already exists"*)  echo "ℹ️  Guard hing schon in diesem Netz." ;;
  *)                   echo "❌ $OUT"; exit 1 ;;
esac

echo "Teste die Leitung (erwartet: status 401) …"
docker exec "$META" node -e "fetch('http://gmail-guard:8000/mcp',{method:'POST'}).then(r=>console.log('status',r.status)).catch(e=>console.log('FEHLER',(e.cause&&e.cause.code)||e.message))"

echo
echo "👉 Jetzt in MetaMCP beim Server auf 'Reconnect' klicken."
echo "👉 Dauerhaft machen: in Coolify beim Guard die Variable  METAMCP_NETWORK=$NET  setzen und neu deployen."
