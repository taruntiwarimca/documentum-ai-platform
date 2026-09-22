import json

import pytest

from agent_common.secrets_client import SecretNotFoundError, resolve_secret


def _vault(tmp_path):
    path = tmp_path / "vault.json"
    path.write_text(
        json.dumps({"dctm": {"oracle": {"admin": "s3cret-not-real"}}}),
        encoding="utf-8",
    )
    return path


def test_resolve_nested_ref(tmp_path):
    assert resolve_secret(_vault(tmp_path), "vault://dctm/oracle/admin") == "s3cret-not-real"


def test_resolve_missing_ref_raises(tmp_path):
    with pytest.raises(SecretNotFoundError):
        resolve_secret(_vault(tmp_path), "vault://dctm/oracle/nope")


def test_resolve_missing_vault_file_raises(tmp_path):
    with pytest.raises(SecretNotFoundError):
        resolve_secret(tmp_path / "does-not-exist.json", "vault://dctm/oracle/admin")


def test_non_vault_ref_raises_value_error(tmp_path):
    with pytest.raises(ValueError):
        resolve_secret(_vault(tmp_path), "plaintext-not-a-ref")
