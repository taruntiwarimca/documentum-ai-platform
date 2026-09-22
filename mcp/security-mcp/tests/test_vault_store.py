from security_mcp.vault_store import put_secret, read_vault


def test_put_creates_nested_structure(tmp_path):
    vault = tmp_path / "vault.json"
    put_secret(vault, "dctm/oracle/admin", "s3cret")
    assert read_vault(vault) == {"dctm": {"oracle": {"admin": "s3cret"}}}


def test_put_merges_with_existing(tmp_path):
    vault = tmp_path / "vault.json"
    put_secret(vault, "dctm/oracle/admin", "one")
    put_secret(vault, "dctm/otds/ldap", "two")
    assert read_vault(vault) == {"dctm": {"oracle": {"admin": "one"}, "otds": {"ldap": "two"}}}


def test_read_missing_vault_returns_empty(tmp_path):
    assert read_vault(tmp_path / "nope.json") == {}
