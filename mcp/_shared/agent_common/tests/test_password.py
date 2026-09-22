from agent_common.password import hash_password, verify_password


def test_verify_correct_password():
    record = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", record["salt"], record["password_hash"])


def test_verify_wrong_password():
    record = hash_password("correct-horse-battery-staple")
    assert not verify_password("wrong", record["salt"], record["password_hash"])


def test_same_password_different_salts_gives_different_hashes():
    a = hash_password("same-password")
    b = hash_password("same-password")
    assert a["salt"] != b["salt"]
    assert a["password_hash"] != b["password_hash"]
