"""Konto im Container verbinden (python -m app.connect) + Schlüssel, die der Server selbst erzeugt."""
import types

import conftest
import pytest
from google.oauth2.credentials import Credentials

from common import secrets_store
from common.tokens import SCOPE_MODIFY, load_accounts


@pytest.fixture()
def C(monkeypatch, tmp_path):
    monkeypatch.setenv("TOKENS_DIR", str(tmp_path / "tokens"))
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "cid")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "csec")
    monkeypatch.setenv("SECRETS_FILE", str(tmp_path / "secrets.json"))
    import app.connect as connect

    class Flow:
        def authorization_url(self, **kw):
            assert kw["access_type"] == "offline" and kw["prompt"] == "consent"
            return "https://accounts.google.com/auth?x=1", "state"

        def fetch_token(self, authorization_response):
            assert authorization_response.startswith("http://localhost:8080/?state=")
            self.credentials = Credentials(token="t", refresh_token="r", client_id="c", client_secret="s",
                                           token_uri="https://oauth2.googleapis.com/token", scopes=[SCOPE_MODIFY])

    monkeypatch.setattr(connect, "_make_flow", lambda *a: Flow())
    monkeypatch.setattr(connect, "_profile_email", lambda creds: "hans@gmail.com")
    return connect


def run(C, argv, answers):
    it, out = iter(answers), []
    code = C.main(argv, ask=lambda *_: next(it), out=out.append)
    return code, "\n".join(map(str, out))


def test_connect_stores_encrypted_account_that_the_server_can_load(C, tmp_path):
    code, text = run(C, ["--mode", "full"], ["privat", "http://localhost:8080/?state=s&code=abc"])
    assert code == 0 and "hans@gmail.com" in text and "https://accounts.google.com/auth" in text
    acc = load_accounts(str(tmp_path / "tokens"), "GUARD_TOKEN_KEY")["privat"]
    assert acc.email == "hans@gmail.com" and acc.can_modify


def test_read_mode_requests_only_read_scope(C, monkeypatch):
    seen = []
    orig = C._make_flow
    monkeypatch.setattr(C, "_make_flow", lambda cid, sec, scopes: (seen.append(scopes), orig(cid, sec, scopes))[1])
    run(C, ["--mode", "read", "--name", "x"], ["http://localhost:8080/?state=s&code=abc"])
    assert seen == [["https://www.googleapis.com/auth/gmail.readonly"]]


def test_missing_google_client_gives_helpful_message(C, monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID")
    code, text = run(C, [], [])
    assert code == 1 and "GOOGLE_CLIENT_ID" in text


def test_bad_name_and_bad_pasted_url_are_rejected(C, monkeypatch):
    assert run(C, ["--name", "Böse Name"], [])[0] == 1
    monkeypatch.setattr(C, "_make_flow", lambda *a: types.SimpleNamespace(
        authorization_url=lambda **k: ("u", "s"),
        fetch_token=lambda authorization_response: (_ for _ in ()).throw(ValueError("bad"))))
    code, text = run(C, ["--name", "x"], ["nonsense"])
    assert code == 1 and "nicht geklappt" in text


def test_show_prints_bearer_that_stays_stable_across_restarts(C, monkeypatch):
    monkeypatch.delenv("MCP_BEARER_TOKEN", raising=False)
    monkeypatch.delenv("GUARD_TOKEN_KEY", raising=False)
    first = run(C, ["--show"], [])[1]
    monkeypatch.delenv("MCP_BEARER_TOKEN"), monkeypatch.delenv("GUARD_TOKEN_KEY")
    second = run(C, ["--show"], [])[1]
    assert first == second and len(first.split(": ")[1]) >= 32


def test_secrets_store_fails_loudly_without_writable_volume(monkeypatch, tmp_path):
    monkeypatch.delenv("GUARD_TOKEN_KEY", raising=False)
    blocker = tmp_path / "file"
    blocker.write_text("x")
    with pytest.raises(SystemExit):
        secrets_store.ensure(("GUARD_TOKEN_KEY",), path=blocker / "secrets.json")
    monkeypatch.delenv("GUARD_TOKEN_KEY", raising=False)


def test_server_picks_up_newly_connected_account_without_restart(monkeypatch, tmp_path):
    monkeypatch.setenv("TOKENS_DIR", str(conftest.TMP / "guard"))
    import app.server as S
    monkeypatch.setattr(S, "TOKENS_DIR", str(tmp_path))
    monkeypatch.setattr(S, "ACCOUNTS", {})
    (tmp_path / "neu.enc").write_bytes(
        __import__("common.tokens", fromlist=["x"]).encrypt_account(
            conftest.GUARD_KEY, "neu", "neu@example.com", [SCOPE_MODIFY], conftest._creds(SCOPE_MODIFY)))
    assert [k["konto"] for k in S.list_accounts()["konten"]] == ["neu"]
