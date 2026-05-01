from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.client_service import create_cloud_client
from app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )
    user = User(
        username=req.username,
        hashed_password=hash_password(req.password),
        display_name=req.display_name or req.username,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create Alibaba Cloud client and bind to local user
    try:
        cloud_client = create_cloud_client(name=user.display_name or user.username)
        user.client_id = cloud_client["id"]
        user.client_uuid = cloud_client["client_uuid"]
        db.commit()
        db.refresh(user)
    except Exception as exc:
        # Rollback local user if cloud client creation fails
        db.delete(user)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to create Alibaba Cloud client: {exc}",
        )

    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
