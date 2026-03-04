import pytest
import jwt

from services.auth_service import AuthService


def test_hash_and_verify_password():
    svc = AuthService(jwt_secret="secret", jwt_expire_days=30)
    hashed = svc.hash_password("mypassword")
    assert hashed != "mypassword"
    assert svc.verify_password("mypassword", hashed)
    assert not svc.verify_password("wrong", hashed)


def test_create_and_decode_token():
    svc = AuthService(jwt_secret="secret", jwt_expire_days=30)
    token = svc.create_token(user_id="user-123")
    user_id = svc.decode_token(token)
    assert user_id == "user-123"


def test_decode_invalid_token_raises():
    svc = AuthService(jwt_secret="secret", jwt_expire_days=30)
    with pytest.raises(jwt.InvalidTokenError):
        svc.decode_token("not.a.token")
