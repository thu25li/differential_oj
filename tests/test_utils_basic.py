from app.utils.time import now_utc
from app.utils.id_gen import generate_uuid
from app.utils.password import hash_password, verify_password


def test_now_utc_format():
    s = now_utc()
    assert s.endswith("Z")
    assert len(s) == 20  # YYYY-MM-DDTHH:MM:SSZ
    assert s[4] == "-" and s[7] == "-" and s[10] == "T"


def test_generate_uuid_unique():
    a = generate_uuid()
    b = generate_uuid()
    assert a != b
    assert len(a) == 36


def test_password_roundtrip():
    h = hash_password("secret123")
    assert h != "secret123"
    assert verify_password("secret123", h) is True
    assert verify_password("wrong", h) is False