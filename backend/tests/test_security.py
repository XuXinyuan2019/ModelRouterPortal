"""Unit tests for app/utils/security.py."""

from datetime import datetime, timedelta

from jose import jwt

from app.config import settings
from app.utils.security import (
    ALGORITHM,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password():
    hashed = hash_password("mysecret")
    assert hashed  # non-empty
    assert hashed != "mysecret"  # not plaintext


def test_verify_password_correct():
    hashed = hash_password("mysecret")
    assert verify_password("mysecret", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("mysecret")
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token():
    token = create_access_token({"sub": 42})
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_access_token():
    token = create_access_token({"sub": 42})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "42"  # sub is cast to str


def test_decode_expired_token():
    """A token with an already-past expiry should return None."""
    to_encode = {"sub": "1"}
    expire = datetime.utcnow() + timedelta(minutes=-1)
    to_encode["exp"] = expire
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    assert decode_access_token(token) is None


def test_decode_invalid_token():
    assert decode_access_token("this-is-not-a-jwt") is None
