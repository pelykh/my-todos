import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from config import Settings, get_settings
from database import get_db
from models import User
from repositories.user_repository import UserRepository
from services.auth_service import AuthService

security = HTTPBearer()


def get_auth_service(settings: Settings = Depends(get_settings)) -> AuthService:
    return AuthService(jwt_secret=settings.jwt_secret, jwt_expire_days=settings.jwt_expire_days)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    auth_svc: AuthService = Depends(get_auth_service),
) -> User:
    try:
        user_id = auth_svc.decode_token(credentials.credentials)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
