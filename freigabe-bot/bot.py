"""freigabe-bot – die EINZIGE Stelle, die senden kann. Und nur nach dem Klick des Besitzers.

Sicherheit:
- reagiert ausschließlich auf TELEGRAM_ALLOWED_USER_ID (den Besitzer)
- zeigt die exakte Mail (An/CC/BCC/Betreff/Text/Anhänge)
- Fingerabdruck (SHA-256): gesendet wird nur, was in der Vorschau stand
"""
import asyncio
import base64
import hashlib
import html
import io
import json
import logging
import os
import time
from datetime import datetime
from datetime import time as dtime
from email import policy
from email.parser import BytesParser
from zoneinfo import ZoneInfo

from googleapiclient.discovery import build
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, filters

from common import store
from common.textutil import html_to_text
from common.tokens import load_accounts

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("freigabe-bot")

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED = int(os.environ["TELEGRAM_ALLOWED_USER_ID"])
TZ = ZoneInfo(os.environ.get("TZ", "Europe/Berlin"))
APPROVAL_TTL = int(os.environ.get("APPROVAL_TTL_HOURS", 24)) * 3600
BULK_TTL = int(os.environ.get("BULK_TTL_HOURS", 2)) * 3600
SUMMARY_HOUR = int(os.environ.get("SUMMARY_HOUR", 20))
PREVIEW_CHARS = 1800

store.init()
ACCOUNTS = load_accounts(os.environ.get("TOKENS_DIR", "/data/tokens"), "BOT_TOKEN_KEY")
ACTION_DE = {"archive": "archivieren", "trash": "in den Papierkorb legen", "spam": "als Spam markieren"}
e = html.escape


# ================================================================ Gmail (synchron, läuft im Thread)
def _svc(account):
    acc = ACCOUNTS.get(account)
    if not acc:
        raise RuntimeError(f"Konto '{account}' ist im Bot nicht eingerichtet.")
    return build("gmail", "v1", credentials=acc.creds, cache_discovery=False), acc


def fetch_draft(account, draft_id):
    svc, _ = _svc(account)
    d = svc.users().drafts().get(userId="me", id=draft_id, format="raw").execute(num_retries=2)
    return d["message"]["raw"], d["message"].get("threadId")


def send_exact(account, draft_id, raw, thread_id):
    """Sendet GENAU die geprüften Bytes und entfernt danach den Entwurf."""
    svc, _ = _svc(account)
    body = {"raw": raw} | ({"threadId": thread_id} if thread_id else {})
    sent = svc.users().messages().send(userId="me", body=body).execute(num_retries=2)
    try:
        svc.users().drafts().delete(userId="me", id=draft_id).execute()
    except Exception:
        pass
    return sent.get("id")


def fingerprint(raw_b64):
    return hashlib.sha256(base64.urlsafe_b64decode(raw_b64 + "=" * (-len(raw_b64) % 4))).hexdigest()


def parse_raw(raw_b64):
    msg = BytesParser(policy=policy.default).parsebytes(
        base64.urlsafe_b64decode(raw_b64 + "=" * (-len(raw_b64) % 4)))
    body = ""
    part = msg.get_body(preferencelist=("plain", "html"))
    if part is not None:
        body = part.get_content()
        if part.get_content_type() == "text/html":
            body = html_to_text(body)
    atts = [a.get_filename() or "(ohne Name)" for a in msg.iter_attachments()]
    return {"to": str(msg.get("To", "")), "cc": str(msg.get("Cc", "")), "bcc": str(msg.get("Bcc", "")),
            "subject": str(msg.get("Subject", "")), "body": body, "atts": atts}


# ================================================================ Anzeige
def approval_text(row, acc, m):
    lines = [
        f"📨 <b>Freigabe #{row['id']}</b> – Hermes möchte senden",
        f"👤 Konto: <b>{e(row['account'])}</b> ({e(acc.email)})",
        "",
        f"➡️ <b>An:</b> {e(m['to'])}",
    ]
    if m["cc"]:
        lines.append(f"👥 <b>CC:</b> {e(m['cc'])}")
    if m["bcc"]:
        lines.append(f"🕶️ <b>BCC (unsichtbar!):</b> {e(m['bcc'])}")
    lines.append(f"📝 <b>Betreff:</b> {e(m['subject'])}")
    if m["atts"]:
        lines.append(f"📎 <b>Anhänge:</b> {e(', '.join(m['atts']))}")
    if row.get("note"):
        lines.append(f"💬 <i>Notiz von Hermes:</i> {e(row['note'])}")
    body = m["body"].strip()
    shown = body[:PREVIEW_CHARS]
    lines += ["", "━━━━━━━━━━━━", e(shown)]
    if len(body) > PREVIEW_CHARS:
        lines.append(f"\n<i>… gekürzt – kompletter Text als Datei oben.</i>")
    return "\n".join(lines)


def approval_buttons(row, acc):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Senden", callback_data=f"ap:ok:{row['id']}"),
         InlineKeyboardButton("❌ Ablehnen", callback_data=f"ap:no:{row['id']}")],
        [InlineKeyboardButton("🔗 In Gmail öffnen", url=f"https://mail.google.com/mail/u/{acc.email}/#drafts")],
    ])


def job_text(job):
    ids = json.loads(job["ids"])
    preview = json.loads(job["preview"] or "[]")
    lines = [
        f"🧹 <b>Masse-Freigabe #{job['id']}</b>",
        f"👤 Konto: <b>{e(job['account'])}</b>",
        f"⚙️ Hermes will <b>{len(ids)} Mails {ACTION_DE.get(job['action'], job['action'])}</b>.",
    ]
    if job.get("reason"):
        lines.append(f"💬 <i>Begründung von Hermes:</i> {e(job['reason'])}")
    lines += ["", "<b>Beispiele:</b>"]
    for p in preview:
        lines.append(f"• {e(p.get('betreff', ''))[:90]} <i>({e(p.get('von', ''))[:50]})</i>")
    if len(ids) > len(preview):
        lines.append(f"<i>… und {len(ids) - len(preview)} weitere</i>")
    return "\n".join(lines)


async def notify(ctx, text):
    await ctx.bot.send_message(chat_id=ALLOWED, text=text, parse_mode=ParseMode.HTML)


# ================================================================ Abfrage-Schleife
async def present_approval(ctx, row):
    try:
        raw, _ = await asyncio.to_thread(fetch_draft, row["account"], row["draft_id"])
        acc = ACCOUNTS[row["account"]]
        m = parse_raw(raw)
    except Exception as ex:
        store.update_approval(row["id"], status="error", info=str(ex)[:300])
        await notify(ctx, f"⚠️ Freigabe #{row['id']} konnte nicht geladen werden: {e(str(ex))[:300]}")
        return
    if len(m["body"]) > PREVIEW_CHARS:
        await ctx.bot.send_document(chat_id=ALLOWED, filename=f"entwurf_{row['id']}.txt",
                                    document=io.BytesIO(m["body"].encode()),
                                    caption=f"Volltext zu Freigabe #{row['id']}")
    msg = await ctx.bot.send_message(chat_id=ALLOWED, text=approval_text(row, acc, m),
                                     parse_mode=ParseMode.HTML, reply_markup=approval_buttons(row, acc),
                                     disable_web_page_preview=True)
    store.update_approval(row["id"], status="pending", hash=fingerprint(raw), tg_message_id=msg.message_id)


async def present_job(ctx, job):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Erlauben", callback_data=f"bj:ok:{job['id']}"),
                                InlineKeyboardButton("❌ Ablehnen", callback_data=f"bj:no:{job['id']}")]])
    msg = await ctx.bot.send_message(chat_id=ALLOWED, text=job_text(job), parse_mode=ParseMode.HTML,
                                     reply_markup=kb)
    store.update_job(job["id"], status="pending", tg_message_id=msg.message_id)


async def close_buttons(ctx, message_id, note):
    if not message_id:
        return
    try:
        await ctx.bot.edit_message_reply_markup(chat_id=ALLOWED, message_id=message_id, reply_markup=None)
        await ctx.bot.send_message(chat_id=ALLOWED, text=note, reply_to_message_id=message_id,
                                   parse_mode=ParseMode.HTML)
    except Exception:
        pass


async def poll(ctx: ContextTypes.DEFAULT_TYPE):
    try:
        for row in store.approvals_with_status("new"):
            await present_approval(ctx, row)
        for job in store.jobs_with_status("new"):
            await present_job(ctx, job)
        now = time.time()
        for row in store.approvals_with_status("pending"):
            if now - row["created"] > APPROVAL_TTL:
                if store.transition_approval(row["id"], "pending", "expired"):
                    await close_buttons(ctx, row["tg_message_id"], "⌛ Abgelaufen – nicht gesendet.")
        for row in store.approvals_with_status("superseded"):
            if row["tg_message_id"]:
                store.update_approval(row["id"], tg_message_id=None)
                await close_buttons(ctx, row["tg_message_id"],
                                    "🔄 Hermes hat den Entwurf geändert – diese Freigabe ist ungültig.")
        for job in store.jobs_with_status("pending"):
            if now - job["created"] > BULK_TTL:
                if store.transition_job(job["id"], "pending", "expired"):
                    await close_buttons(ctx, job["tg_message_id"], "⌛ Abgelaufen – nichts passiert.")
    except Exception:
        log.exception("Fehler in der Abfrage-Schleife")


# ================================================================ Klicks
async def on_click(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id != ALLOWED:
        store.audit("bot", "unauthorized_click", detail=str(q.from_user.id))
        await q.answer("Nicht erlaubt.", show_alert=True)
        return
    kind, decision, sid = q.data.split(":")
    rid = int(sid)
    stamp = datetime.now(TZ).strftime("%H:%M")

    async def finish(note):
        await q.answer()
        try:
            await q.edit_message_text(q.message.text_html + f"\n\n{note}", parse_mode=ParseMode.HTML,
                                      disable_web_page_preview=True)
        except Exception:
            await close_buttons(ctx, q.message.message_id, note)

    if kind == "ap":
        row = store.get_approval(rid)
        if not row or row["status"] != "pending":
            return await finish(f"ℹ️ Nicht mehr offen (Status: {row['status'] if row else '?'}).")
        if decision == "no":
            store.transition_approval(rid, "pending", "rejected")
            store.audit("oliver", "reject_send", row["account"], 1, target=row["draft_id"])
            return await finish(f"❌ <b>Abgelehnt</b> {stamp} – Entwurf bleibt in Gmail.")
        if not store.transition_approval(rid, "pending", "sending"):
            return await finish("ℹ️ Wird bereits verarbeitet.")
        try:
            raw, thread_id = await asyncio.to_thread(fetch_draft, row["account"], row["draft_id"])
            if fingerprint(raw) != row["hash"]:
                store.update_approval(rid, status="changed")
                store.audit("bot", "send_blocked_changed", row["account"], 1, target=row["draft_id"])
                return await finish("⚠️ <b>NICHT gesendet:</b> Der Entwurf wurde nach der Vorschau verändert.")
            sent_id = await asyncio.to_thread(send_exact, row["account"], row["draft_id"], raw, thread_id)
        except Exception as ex:
            store.update_approval(rid, status="error", info=str(ex)[:300])
            return await finish(f"⚠️ Fehler, nicht gesendet: {e(str(ex))[:200]}")
        store.update_approval(rid, status="sent", info=sent_id)
        store.remove_hermes_draft(row["account"], row["draft_id"])
        store.audit("oliver", "send", row["account"], 1, target=sent_id, detail=f"Freigabe #{rid}")
        return await finish(f"✅ <b>Gesendet</b> um {stamp}")

    if kind == "bj":
        job = store.get_job(rid)
        if not job or job["status"] != "pending":
            return await finish(f"ℹ️ Nicht mehr offen (Status: {job['status'] if job else '?'}).")
        if decision == "no":
            store.transition_job(rid, "pending", "rejected", decided=time.time())
            store.audit("oliver", f"reject_bulk_{job['action']}", job["account"], 1, target=str(rid))
            return await finish(f"❌ <b>Abgelehnt</b> {stamp} – nichts passiert.")
        store.transition_job(rid, "pending", "approved", decided=time.time())
        store.audit("oliver", f"approve_bulk_{job['action']}", job["account"], 1, target=str(rid))
        return await finish(f"✅ <b>Erlaubt</b> {stamp} – Hermes darf jetzt ausführen "
                            f"(gültig {BULK_TTL // 3600} Std.).")


# ================================================================ Befehle
async def cmd_start(update: Update, ctx):
    await update.message.reply_text(
        "👋 Freigabe-Bot läuft.\n\n"
        "/status – offene Anfragen\n"
        "/stopp – NOT-AUS: Hermes kann gar nichts mehr in Gmail\n"
        "/weiter – Not-Aus aufheben\n"
        "/heute – Bericht für heute")


async def cmd_status(update: Update, ctx):
    ap = len(store.approvals_with_status("pending")) + len(store.approvals_with_status("new"))
    jb = len(store.jobs_with_status("pending")) + len(store.jobs_with_status("new"))
    paused = "🛑 NOT-AUS AKTIV" if store.is_paused() else "🟢 aktiv"
    konten = ", ".join(f"{a.name} ({a.email})" for a in ACCOUNTS.values()) or "keine"
    await update.message.reply_text(f"Status: {paused}\n📨 Offene Sende-Freigaben: {ap}\n"
                                    f"🧹 Offene Masse-Freigaben: {jb}\n👤 Konten: {konten}")


async def cmd_stop(update: Update, ctx):
    store.set_setting("paused", "1")
    store.audit("oliver", "pause")
    await update.message.reply_text("🛑 NOT-AUS aktiv. Hermes kann weder lesen noch ändern. /weiter zum Aufheben.")


async def cmd_resume(update: Update, ctx):
    store.set_setting("paused", "0")
    store.audit("oliver", "resume")
    await update.message.reply_text("🟢 gmail-guard läuft wieder.")


def summary_text(since, title):
    rows = store.summary_since(since)
    if not rows:
        return f"📊 <b>{title}</b>\nKeine Aktivität. 😴"
    names = {
        "search": "🔎 gesucht", "read": "📖 gelesen", "read_thread": "🧵 Verläufe gelesen",
        "read_attachment": "📎 Anhänge gelesen", "labels": "🏷️ Labels geändert", "archive": "📦 archiviert",
        "trash": "🗑️ Papierkorb", "spam": "🚫 Spam", "untrash": "♻️ wiederhergestellt",
        "create_draft": "✍️ Entwürfe", "update_draft": "✏️ Entwürfe geändert", "send": "✅ gesendet (von dir)",
        "reject_send": "❌ Senden abgelehnt", "send_blocked_changed": "⚠️ Senden blockiert (geändert)",
        "unauthorized_click": "🚨 FREMDE KLICKS",
    }
    out, current = [f"📊 <b>{title}</b>"], None
    for r in rows:
        if r["action"] not in names:
            continue
        if r["account"] != current:
            current = r["account"]
            out.append(f"\n👤 <b>{e(current or 'System')}</b>")
        out.append(f"  {names[r['action']]}: {r['n']}")
    return "\n".join(out)


def _midnight():
    return datetime.now(TZ).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()


async def cmd_today(update: Update, ctx):
    await update.message.reply_text(summary_text(_midnight(), "Heute"), parse_mode=ParseMode.HTML)


async def daily_summary(ctx):
    await notify(ctx, summary_text(_midnight(), "Tagesbericht gmail-guard"))


# ================================================================ Start
def main():
    app = Application.builder().token(TOKEN).build()
    me = filters.User(user_id=ALLOWED)
    app.add_handler(CommandHandler("start", cmd_start, filters=me))
    app.add_handler(CommandHandler("status", cmd_status, filters=me))
    app.add_handler(CommandHandler("stopp", cmd_stop, filters=me))
    app.add_handler(CommandHandler("weiter", cmd_resume, filters=me))
    app.add_handler(CommandHandler("heute", cmd_today, filters=me))
    app.add_handler(CallbackQueryHandler(on_click, pattern=r"^(ap|bj):(ok|no):\d+$"))
    app.job_queue.run_repeating(poll, interval=5, first=3)
    app.job_queue.run_daily(daily_summary, time=dtime(hour=SUMMARY_HOUR, tzinfo=TZ))
    log.info("freigabe-bot startet | Konten: %s", ", ".join(ACCOUNTS) or "KEINE")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
