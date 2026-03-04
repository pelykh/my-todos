from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from repositories.user_repository import UserRepository
from routers.deps import get_auth_service
from schemas import LoginRequest, RegisterRequest, TokenResponse
from services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(
    body: RegisterRequest,
    db: Session = Depends(get_db),
    auth_svc: AuthService = Depends(get_auth_service),
):
    repo = UserRepository(db)
    if repo.get_by_email(body.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = repo.create(email=body.email, password_hash=auth_svc.hash_password(body.password))
    return TokenResponse(access_token=auth_svc.create_token(user.id))


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
    auth_svc: AuthService = Depends(get_auth_service),
):
    repo = UserRepository(db)
    user = repo.get_by_email(body.email)
    if user is None or not auth_svc.verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=auth_svc.create_token(user.id))
