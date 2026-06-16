from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.security.jwt import create_access_token, hash_password, verify_password
from app.db.connection import get_db
from app.db.models import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SendCodeRequest,
)
from app.services.membership import serialize_user
from app.services.verification import VerificationError, send_code, verify_code

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/send-code")
def send_verification_code(req: SendCodeRequest, db: Session = Depends(get_db)):
    email = req.email
    purpose = req.purpose.value

    existing = db.query(User).filter(User.email == email).first()
    if purpose == "register" and existing:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": "该邮箱已注册"},
        )
    if purpose in ("login", "reset_password") and not existing:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": "该邮箱尚未注册"},
        )

    try:
        send_code(db, email, purpose)
    except VerificationError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"success": False, "error": exc.message},
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail={"success": False, "error": str(exc)},
        ) from exc

    return {"success": True, "message": "验证码已发送，请查收邮件"}


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    email = req.email
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": "该邮箱已注册"},
        )

    try:
        verify_code(db, email, "register", req.code)
    except VerificationError as exc:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": exc.message},
        ) from exc

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
    email = req.email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail={"success": False, "error": "邮箱或密码错误"},
        )

    if req.code:
        try:
            verify_code(db, email, "login", req.code)
        except VerificationError as exc:
            raise HTTPException(
                status_code=401,
                detail={"success": False, "error": exc.message},
            ) from exc
    elif not verify_password(req.password, user.password_hash):
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


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    email = req.email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": "该邮箱尚未注册"},
        )

    try:
        verify_code(db, email, "reset_password", req.code)
    except VerificationError as exc:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": exc.message},
        ) from exc

    user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"success": True, "message": "密码已重置，请使用新密码登录"}


@router.get("/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"success": True, "data": serialize_user(db, user)}
