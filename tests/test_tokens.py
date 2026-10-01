"""Accounts can come from files OR from an environment variable (Coolify has no files)."""
import conftest
from common.tokens import SCOPE_MODIFY, encrypt_account, load_accounts


def _blob(name, email):
    return encrypt_account(conftest.GUARD_KEY, name, email, [SCOPE_MODIFY],
                           conftest._creds(SCOPE_MODIFY)).decode()


def test_accounts_load_from_env_var(monkeypatch, tmp_path):
    monkeypatch.setenv("TEST_ACCOUNTS", f"{_blob('privat', 'a@example.com')}, {_blob('firma', 'b@example.com')}")
    accs = load_accounts(str(tmp_path), "GUARD_TOKEN_KEY", "TEST_ACCOUNTS")
    assert sorted(accs) == ["firma", "privat"]
    assert accs["firma"].email == "b@example.com" and accs["firma"].can_modify


def test_env_and_files_can_be_mixed(monkeypatch):
    monkeypatch.setenv("TEST_ACCOUNTS", _blob("extra", "c@example.com"))
    accs = load_accounts(str(conftest.TMP / "guard"), "GUARD_TOKEN_KEY", "TEST_ACCOUNTS")
    assert sorted(accs) == ["extra", "privat"]


def test_no_accounts_is_fine(monkeypatch, tmp_path):
    monkeypatch.delenv("TEST_ACCOUNTS", raising=False)
    assert load_accounts(str(tmp_path), "GUARD_TOKEN_KEY", "TEST_ACCOUNTS") == {}
