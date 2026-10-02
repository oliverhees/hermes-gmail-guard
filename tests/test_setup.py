"""The setup wizard: answers in → env files out, second run adds an account and keeps the keys."""
import json

import conftest
import pytest
from cryptography.fernet import Fernet

import setup as wizard  # scripts/setup.py
from common.tokens import SCOPE_COMPOSE, SCOPE_MODIFY, load_accounts


@pytest.fixture()
def run(monkeypatch, tmp_path):
    secret = tmp_path / "client_secret_x.json"
    secret.write_text("{}")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(wizard, "ROOT", tmp_path)
    (tmp_path / "guard.env.example").write_text((conftest.ROOT / "guard.env.example").read_text())
    (tmp_path / "bot.env.example").write_text((conftest.ROOT / "bot.env.example").read_text())

    import add_account
    monkeypatch.setattr(add_account, "login", lambda cs, scopes, hint: (
        conftest._creds(scopes[0]), "hans@gmail.com" if "hans" in cs_name[0] else "anna@gmail.com"))
    cs_name = [""]

    def go(answers, who="hans"):
        cs_name[0] = who
        it = iter(answers)
        monkeypatch.setattr("builtins.input", lambda *_: next(it))
        wizard.main(out=tmp_path / "out")
        return tmp_path
    go.secret = str(secret)
    return go


BOT_YES = ["2", "123456789:AAEhBP0av28sample_token_value_xx", "4242"]   # Senden per Telegram


def test_first_run_local_writes_env_files_with_working_accounts(run):
    d = run(["2", "privat", run.secret, "3"] + BOT_YES)
    guard, bot = (d / "guard.env").read_text(), (d / "bot.env").read_text()
    assert "GUARD_MODE=full" in guard and "GUARD_ACCOUNTS=gAAAA" in guard
    assert "TELEGRAM_ALLOWED_USER_ID=4242" in bot and "BOT_ACCOUNTS=gAAAA" in bot
    assert "TELEGRAM_BOT_TOKEN" not in guard      # Bot-Schlüssel gehören nicht in den guard
    assert oct((d / "guard.env").stat().st_mode & 0o777) == "0o600"
    env = wizard.read_env(d / "out" / "settings.env")
    import os
    os.environ["G"], os.environ["B"] = env["GUARD_ACCOUNTS"], env["BOT_ACCOUNTS"]
    os.environ["GK"], os.environ["BK"] = env["GUARD_TOKEN_KEY"], env["BOT_TOKEN_KEY"]
    g = load_accounts(str(d), "GK", "G")["privat"]
    b = load_accounts(str(d), "BK", "B")["privat"]
    assert (g.email, g.scopes) == ("hans@gmail.com", [SCOPE_MODIFY])
    assert b.scopes == [SCOPE_COMPOSE]


def test_server_mode_writes_only_the_coolify_file(run):
    d = run(["1", "privat", run.secret, "2", "2", "123456789:AAEhBP0av28sample_token_value_xx", "4242"])
    assert not (d / "guard.env").exists()
    env = wizard.read_env(d / "out" / "settings.env")
    assert env["GUARD_MODE"] == "organize" and "BOT_ACCOUNTS" not in env


def test_second_run_adds_account_and_keeps_keys(run):
    d = run(["1", "privat", run.secret, "3"] + BOT_YES)
    first = wizard.read_env(d / "out" / "settings.env")
    run(["1", "firma", run.secret, "3"], who="anna")        # kein Telegram-Prompt mehr
    second = wizard.read_env(d / "out" / "settings.env")
    for k in ("GUARD_TOKEN_KEY", "BOT_TOKEN_KEY", "MCP_BEARER_TOKEN", "TELEGRAM_BOT_TOKEN"):
        assert first[k] == second[k]
    f = Fernet(second["GUARD_TOKEN_KEY"].encode())
    names = sorted(json.loads(f.decrypt(b.encode()))["name"] for b in second["GUARD_ACCOUNTS"].split(","))
    assert names == ["firma", "privat"]


def test_reconnecting_same_name_replaces_instead_of_duplicating(run):
    d = run(["1", "privat", run.secret, "3"] + BOT_YES)
    run(["1", "privat", run.secret, "3"])
    assert len(wizard.read_env(d / "out" / "settings.env")["GUARD_ACCOUNTS"].split(",")) == 1


def test_default_is_no_bot_send_in_gmail_only(run):
    d = run(["2", "privat", run.secret, "3", "1"])          # 5: nur in Gmail senden
    env = wizard.read_env(d / "out" / "settings.env")
    assert env["APPROVAL_BOT"] == "0"
    assert "BOT_TOKEN_KEY" not in env and "BOT_ACCOUNTS" not in env and "TELEGRAM_BOT_TOKEN" not in env
    assert "APPROVAL_BOT=0" in (d / "guard.env").read_text()
    assert not (d / "bot.env").exists()
