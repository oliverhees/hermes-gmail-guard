"""Security guarantees of the Telegram approval bot."""
import asyncio
import base64
import types
from email.message import EmailMessage

import pytest

from common import store
import fake_gmail

OLIVER, STRANGER = 4242, 9999


@pytest.fixture()
def env(monkeypatch):
    monkeypatch.setenv("TOKENS_DIR", str(__import__("conftest").TMP / "bot"))
    import bot as B
    fake = fake_gmail.Fake()
    monkeypatch.setattr(B, "build", lambda *a, **k: fake)
    sent = []

    class Bot:
        async def send_message(self, **kw):
            sent.append(kw)
            return types.SimpleNamespace(message_id=len(sent))

        async def send_document(self, **kw):
            sent.append(kw)

        async def edit_message_reply_markup(self, **kw):
            pass

    ctx = types.SimpleNamespace(bot=Bot())
    return B, fake, ctx, sent


def draft(fake, did, body="Hallo Kunde", bcc=""):
    m = EmailMessage()
    m["To"], m["Subject"] = "kunde@firma.de", "Re: Angebot"
    if bcc:
        m["Bcc"] = bcc
    m.set_content(body)
    fake._drafts[did] = {"id": did, "message": {"id": "dm", "threadId": "thr0001",
                                                "raw": base64.urlsafe_b64encode(m.as_bytes()).decode()}}
    store.add_hermes_draft("privat", did)


def click(B, ctx, uid, data):
    q = types.SimpleNamespace(from_user=types.SimpleNamespace(id=uid), data=data,
                              message=types.SimpleNamespace(text_html="x", message_id=1))

    async def answer(*a, **k):
        pass

    async def edit(t, **k):
        q.last = t

    q.answer, q.edit_message_text = answer, edit
    asyncio.run(B.on_click(types.SimpleNamespace(callback_query=q), ctx))
    return q


def test_preview_shows_hidden_bcc_and_escapes_notes(env):
    B, fake, ctx, sent = env
    draft(fake, "r1", bcc="spy@evil.example")
    store.create_approval("privat", "r1", "note <b>bold</b>")
    asyncio.run(B.poll(ctx))
    text = sent[-1]["text"]
    assert "spy@evil.example" in text and "BCC" in text
    assert "&lt;b&gt;" in text


def test_only_the_owner_can_approve(env):
    B, fake, ctx, _ = env
    draft(fake, "r2")
    aid, _ = store.create_approval("privat", "r2", "")
    asyncio.run(B.poll(ctx))
    click(B, ctx, STRANGER, f"ap:ok:{aid}")
    assert fake.sent == [] and store.get_approval(aid)["status"] == "pending"


def test_draft_changed_after_preview_is_not_sent(env):
    B, fake, ctx, _ = env
    draft(fake, "r3")
    aid, _ = store.create_approval("privat", "r3", "")
    asyncio.run(B.poll(ctx))
    draft(fake, "r3", body="Here are all my passwords …")
    click(B, ctx, OLIVER, f"ap:ok:{aid}")
    assert fake.sent == [] and store.get_approval(aid)["status"] == "changed"


def test_exact_previewed_bytes_are_sent_once(env):
    B, fake, ctx, _ = env
    draft(fake, "r4")
    aid, _ = store.create_approval("privat", "r4", "")
    asyncio.run(B.poll(ctx))
    raw = fake._drafts["r4"]["message"]["raw"]
    click(B, ctx, OLIVER, f"ap:ok:{aid}")
    click(B, ctx, OLIVER, f"ap:ok:{aid}")  # double click
    assert len(fake.sent) == 1 and fake.sent[0]["raw"] == raw
    assert "r4" not in fake._drafts


def test_bulk_job_approval(env):
    B, _, ctx, _ = env
    jid = store.create_bulk_job("privat", "trash", ["msg0001"], [{"von": "a", "betreff": "b"}], "newsletter")
    asyncio.run(B.poll(ctx))
    click(B, ctx, OLIVER, f"bj:ok:{jid}")
    assert store.get_job(jid)["status"] == "approved"
