"""Gemeinsame Datenbank für gmail-guard und freigabe-bot.

Liegt auf einem Docker-Volume, das NUR diese beiden Container sehen.
Hermes hat keinen Zugriff darauf.
"""
import json
import os
import sqlite3
import time
from contextlib import contextmanager

DB_PATH = os.environ.get("DB_PATH", "/shared/guard.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    actor TEXT NOT NULL,
    account TEXT,
    action TEXT NOT NULL,
    count INTEGER NOT NULL DEFAULT 1,
    target TEXT,
    detail TEXT,
    via_job INTEGER
);
CREATE INDEX IF NOT EXISTS idx_audit ON audit(account, action, ts);

CREATE TABLE IF NOT EXISTS approvals(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created REAL NOT NULL,
    updated REAL NOT NULL,
    account TEXT NOT NULL,
    draft_id TEXT NOT NULL,
    note TEXT,
    status TEXT NOT NULL,          -- new, pending, sending, sent, rejected, expired, changed, superseded, error
    hash TEXT,
    tg_message_id INTEGER,
    info TEXT
);

CREATE TABLE IF NOT EXISTS bulk_jobs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created REAL NOT NULL,
    updated REAL NOT NULL,
    account TEXT NOT NULL,
    action TEXT NOT NULL,
    ids TEXT NOT NULL,
    preview TEXT,
    reason TEXT,
    status TEXT NOT NULL,          -- new, pending, approved, executing, executed, rejected, expired, error
    decided REAL,
    tg_message_id INTEGER
);

CREATE TABLE IF NOT EXISTS hermes_drafts(
    account TEXT NOT NULL,
    draft_id TEXT NOT NULL,
    created REAL NOT NULL,
    PRIMARY KEY(account, draft_id)
);

CREATE TABLE IF NOT EXISTS settings(
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


@contextmanager
def db():
    con = sqlite3.connect(DB_PATH, timeout=15, isolation_level=None)
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA busy_timeout=15000")
        yield con
    finally:
        con.close()


def init():
    with db() as con:
        con.executescript(SCHEMA)


# ---------------------------------------------------------------- Protokoll
def audit(actor, action, account=None, count=1, target=None, detail=None, via_job=None):
    with db() as con:
        con.execute(
            "INSERT INTO audit(ts, actor, account, action, count, target, detail, via_job) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (time.time(), actor, account, action, count,
             (target or "")[:500], (detail or "")[:1000], via_job),
        )


def count_actions(account, action, since):
    """Zählt Aktionen OHNE Masse-Freigabe (via_job IS NULL) seit Zeitpunkt."""
    with db() as con:
        row = con.execute(
            "SELECT COALESCE(SUM(count),0) AS n FROM audit "
            "WHERE account=? AND action=? AND ts>=? AND via_job IS NULL",
            (account, action, since),
        ).fetchone()
        return int(row["n"])


def summary_since(since):
    with db() as con:
        return [dict(r) for r in con.execute(
            "SELECT account, action, SUM(count) AS n FROM audit WHERE ts>=? "
            "GROUP BY account, action ORDER BY account, action",
            (since,),
        ).fetchall()]


# ---------------------------------------------------------------- Not-Aus
def set_setting(key, value):
    with db() as con:
        con.execute("INSERT INTO settings(key,value) VALUES(?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))


def get_setting(key, default=None):
    with db() as con:
        row = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default


def is_paused():
    return get_setting("paused", "0") == "1"


# ---------------------------------------------------------------- Freigaben (Senden)
def create_approval(account, draft_id, note):
    now = time.time()
    with db() as con:
        existing = con.execute(
            "SELECT id FROM approvals WHERE account=? AND draft_id=? AND status IN ('new','pending')",
            (account, draft_id),
        ).fetchone()
        if existing:
            return int(existing["id"]), False
        cur = con.execute(
            "INSERT INTO approvals(created, updated, account, draft_id, note, status) "
            "VALUES (?,?,?,?,?, 'new')",
            (now, now, account, draft_id, (note or "")[:300]),
        )
        return int(cur.lastrowid), True


def get_approval(approval_id):
    with db() as con:
        row = con.execute("SELECT * FROM approvals WHERE id=?", (approval_id,)).fetchone()
        return dict(row) if row else None


def approvals_with_status(status):
    with db() as con:
        return [dict(r) for r in con.execute(
            "SELECT * FROM approvals WHERE status=? ORDER BY id", (status,)).fetchall()]


def update_approval(approval_id, **fields):
    fields["updated"] = time.time()
    cols = ", ".join(f"{k}=?" for k in fields)
    with db() as con:
        con.execute(f"UPDATE approvals SET {cols} WHERE id=?", (*fields.values(), approval_id))


def transition_approval(approval_id, old, new):
    """Atomarer Statuswechsel. True nur, wenn der alte Status noch stimmte."""
    with db() as con:
        cur = con.execute(
            "UPDATE approvals SET status=?, updated=? WHERE id=? AND status=?",
            (new, time.time(), approval_id, old))
        return cur.rowcount == 1


def supersede_approvals(account, draft_id):
    with db() as con:
        con.execute(
            "UPDATE approvals SET status='superseded', updated=? "
            "WHERE account=? AND draft_id=? AND status IN ('new','pending')",
            (time.time(), account, draft_id))


# ---------------------------------------------------------------- Masse-Jobs
def create_bulk_job(account, action, ids, preview, reason):
    now = time.time()
    with db() as con:
        cur = con.execute(
            "INSERT INTO bulk_jobs(created, updated, account, action, ids, preview, reason, status) "
            "VALUES (?,?,?,?,?,?,?, 'new')",
            (now, now, account, action, json.dumps(ids), json.dumps(preview, ensure_ascii=False),
             (reason or "")[:300]),
        )
        return int(cur.lastrowid)


def get_job(job_id):
    with db() as con:
        row = con.execute("SELECT * FROM bulk_jobs WHERE id=?", (job_id,)).fetchone()
        return dict(row) if row else None


def jobs_with_status(status):
    with db() as con:
        return [dict(r) for r in con.execute(
            "SELECT * FROM bulk_jobs WHERE status=? ORDER BY id", (status,)).fetchall()]


def update_job(job_id, **fields):
    fields["updated"] = time.time()
    cols = ", ".join(f"{k}=?" for k in fields)
    with db() as con:
        con.execute(f"UPDATE bulk_jobs SET {cols} WHERE id=?", (*fields.values(), job_id))


def transition_job(job_id, old, new, **extra):
    extra["updated"] = time.time()
    cols = ", ".join(f"{k}=?" for k in extra)
    with db() as con:
        cur = con.execute(
            f"UPDATE bulk_jobs SET status=?, {cols} WHERE id=? AND status=?",
            (new, *extra.values(), job_id, old))
        return cur.rowcount == 1


# ---------------------------------------------------------------- Hermes-Entwürfe
def add_hermes_draft(account, draft_id):
    with db() as con:
        con.execute("INSERT OR IGNORE INTO hermes_drafts(account, draft_id, created) VALUES (?,?,?)",
                    (account, draft_id, time.time()))


def is_hermes_draft(account, draft_id):
    with db() as con:
        return con.execute("SELECT 1 FROM hermes_drafts WHERE account=? AND draft_id=?",
                           (account, draft_id)).fetchone() is not None


def list_hermes_drafts(account):
    with db() as con:
        return [r["draft_id"] for r in con.execute(
            "SELECT draft_id FROM hermes_drafts WHERE account=? ORDER BY created DESC", (account,))]


def remove_hermes_draft(account, draft_id):
    with db() as con:
        con.execute("DELETE FROM hermes_drafts WHERE account=? AND draft_id=?", (account, draft_id))
