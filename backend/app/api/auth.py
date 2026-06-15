from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.security.jwt import create_access_token, hash_password, verify_password
from app.db.connection import get_db
from app.db.models import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.membership import serialize_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": "该邮箱已注册"},
        )
    user = User(email=email, password_hash=hash_password(req.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id, user.email)
    return {
        "success": True,
        "data": {
            "token": token,
            "user": serialize_user(db, user),
        },
    }


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail={"success": False, "error": "邮箱或密码错误"},
        )
    token = create_access_token(user.id, user.email)
    return {
        "success": True,
        "data": {
            "token": token,
            "user": serialize_user(db, user),
        },
    }


@router.get("/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"success": True, "data": serialize_user(db, user)}
