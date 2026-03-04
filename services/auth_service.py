from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext


class AuthService:
    def __init__(self, jwt_secret: str, jwt_expire_days: int) -> None:
        self._secret = jwt_secret
        self._expire_days = jwt_expire_days
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        return self._pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return self._pwd_context.verify(plain, hashed)

    def create_token(self, user_id: str) -> str:
        payload = {
            "sub": user_id,
            "exp": datetime.now(timezone.utc) + timedelta(days=self._expire_days),
        }
        return jwt.encode(payload, self._secret, algorithm="HS256")

    def decode_token(self, token: str) -> str:
        payload = jwt.decode(token, self._secret, algorithms=["HS256"])
        return payload["sub"]
