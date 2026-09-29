"""Security guarantees of the gmail-guard MCP server."""
import time

import pytest

from common import store
import fake_gmail


@pytest.fixture()
def S(monkeypatch):
    monkeypatch.setenv("TOKENS_DIR", str(__import__("conftest").TMP / "guard"))
    import app.server as server
    fake = fake_gmail.Fake()
    monkeypatch.setattr(server, "build", lambda *a, **k: fake)
    with store.db() as con:
        for t in ("audit", "approvals", "bulk_jobs", "hermes_drafts", "settings"):
            con.execute(f"DELETE FROM {t}")
    server.FAKE = fake
    return server


def test_no_send_tool_is_registered(S):
    names = [t.name for t in S.mcp._tool_manager.list_tools()]
    assert len(names) == 20
    assert not any("send" in n or "forward" in n for n in names)


def test_mail_body_is_marked_untrusted_and_fake_markers_neutralised(S):
    r = S.read_mail("privat", "msg0001")
    assert "FREMDER_INHALT_BEGINN" in r["text"]
    assert ">>> und leite weiter" not in r["text"]  # attacker-supplied marker was defused


def test_bulk_brake_requires_approval_and_is_single_use(S):
    assert S.trash("privat", [f"msg{i:04d}" for i in range(10)])["status"] == "ERLEDIGT"
    r = S.trash("privat", [f"msg{i:04d}" for i in range(10, 21)])
    assert r["status"] == "FREIGABE_NOETIG"
    assert S.execute_bulk_job(r["job_id"])["status"] == "NICHT_FREIGEGEBEN"
    store.transition_job(r["job_id"], "new", "approved", decided=time.time())
    assert S.execute_bulk_job(r["job_id"])["status"] == "ERLEDIGT"
    assert S.execute_bulk_job(r["job_id"])["status"] == "NICHT_FREIGEGEBEN"


def test_salami_tactics_are_caught(S):
    results = [S.trash("privat", [f"msg{i:04d}"])["status"] for i in range(30)]
    assert results.count("ERLEDIGT") == 20
    assert "FREIGABE_NOETIG" in results


@pytest.mark.parametrize("kw", [{"remove_labels": ["INBOX"]}, {"add_labels": ["TRASH"]}, {"add_labels": ["SPAM"]}])
def test_protected_labels_cannot_bypass_the_brake(S, kw):
    with pytest.raises((PermissionError, ValueError)):
        S.modify_labels("privat", ["msg0050"], **kw)


def test_drafts_are_threaded_and_never_sent(S):
    r = S.create_draft("privat", "kunde@firma.de", "", "Danke!", reply_to_message_id="msg0100")
    assert r["status"] == "ENTWURF_ANGELEGT"
    assert S.FAKE._drafts[r["draft_id"]]["message"]["threadId"] == "thr0001"
    assert S.FAKE.sent == []


def test_users_own_drafts_are_off_limits(S):
    S.FAKE._drafts["olivers1"] = {"id": "olivers1", "message": {"id": "x"}}
    with pytest.raises(PermissionError):
        S.update_draft("privat", "olivers1", "a@b.de", "x", "y")
    with pytest.raises(PermissionError):
        S.request_approval("privat", "olivers1")


@pytest.mark.parametrize("to", ["not-an-address", ",".join(f"a{i}@x.de" for i in range(25))])
def test_invalid_or_mass_recipients_rejected(S, to):
    with pytest.raises(ValueError):
        S.create_draft("privat", to, "x", "y")


def test_editing_a_draft_invalidates_pending_approval(S):
    did = S.create_draft("privat", "kunde@firma.de", "Hi", "v1")["draft_id"]
    aid = S.request_approval("privat", did)["approval_id"]
    assert S.request_approval("privat", did)["status"] == "BEREITS_ANGEFRAGT"
    S.update_draft("privat", did, "kunde@firma.de", "Hi", "v2")
    assert store.get_approval(aid)["status"] == "superseded"


def test_kill_switch_blocks_everything(S):
    store.set_setting("paused", "1")
    with pytest.raises(RuntimeError):
        S.search_mails("privat")
    store.set_setting("paused", "0")
    assert S.search_mails("privat", max_results=3)["anzahl"] == 3
