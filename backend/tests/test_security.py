import pytest
import jwt

from app.services.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


def test_password_is_hashed():
    password = "SyntheticTestPassword123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)


def test_wrong_password_is_rejected():
    hashed = hash_password("SyntheticTestPassword123!")

    assert not verify_password("WrongSyntheticPassword!", hashed)


def test_empty_password_is_rejected():
    with pytest.raises(ValueError):
        hash_password("")


def test_password_over_72_bytes_is_rejected():
    with pytest.raises(ValueError):
        hash_password("a" * 73)


def test_password_over_72_bytes_fails_verification():
    hashed = hash_password("SyntheticTestPassword123!")

    assert not verify_password("a" * 73, hashed)


def test_access_token_can_be_created_and_decoded(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "synthetic-test-secret-key-at-least-32-characters-long",
    )

    user_id = "00000000-0000-0000-0000-000000000001"
    token = create_access_token(user_id)
    payload = decode_access_token(token)

    assert payload["sub"] == user_id
    assert "iat" in payload
    assert "exp" in payload


def test_invalid_token_is_rejected(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "synthetic-test-secret-key-at-least-32-characters-long",
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("not-a-valid-token")


def test_missing_jwt_secret_is_rejected(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError):
        create_access_token("00000000-0000-0000-0000-000000000001")


def test_short_jwt_secret_is_rejected(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "too-short")

    with pytest.raises(RuntimeError):
        create_access_token("00000000-0000-0000-0000-000000000001")
