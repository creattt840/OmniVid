import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security.jwt import hash_password, verify_password
from app.db.models import EmailVerificationCode
from app.services.email import send_verification_email

MAX_VERIFY_ATTEMPTS = 5

VALID_PURPOSES = frozenset({"register", "login", "reset_password"})


class VerificationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_expires(expires_at: datetime) -> datetime:
    if expires_at.tzinfo is None:
        return expires_at.replace(tzinfo=timezone.utc)
    return expires_at


def generate_code() -> str:
    settings = get_settings()
    length = settings.verify_code_length
    return "".join(str(secrets.randbelow(10)) for _ in range(length))


def _check_resend_limit(db: Session, email: str, purpose: str) -> None:
    settings = get_settings()
    cutoff = _utcnow() - timedelta(seconds=settings.verify_code_resend_seconds)
    recent = (
        db.query(EmailVerificationCode)
        .filter(
            EmailVerificationCode.email == email,
            EmailVerificationCode.purpose == purpose,
            EmailVerificationCode.created_at >= cutoff,
        )
        .order_by(EmailVerificationCode.created_at.desc())
        .first()
    )
    if recent:
        raise VerificationError(
            f"请 {settings.verify_code_resend_seconds} 秒后再试",
            status_code=429,
        )


def send_code(db: Session, email: str, purpose: str) -> str:
    if purpose not in VALID_PURPOSES:
        raise VerificationError("无效的验证码用途")

    _check_resend_limit(db, email, purpose)

    settings = get_settings()
    code = generate_code()
    expires_at = _utcnow() + timedelta(minutes=settings.verify_code_expire_minutes)

    record = EmailVerificationCode(
        email=email,
        purpose=purpose,
        code_hash=hash_password(code),
        expires_at=expires_at,
    )
    db.add(record)
    db.commit()

    try:
        send_verification_email(email, code, purpose)
    except RuntimeError:
        db.delete(record)
        db.commit()
        raise

    return code


def verify_code(db: Session, email: str, purpose: str, code: str) -> None:
    record = (
        db.query(EmailVerificationCode)
        .filter(
            EmailVerificationCode.email == email,
            EmailVerificationCode.purpose == purpose,
            EmailVerificationCode.used_at.is_(None),
        )
        .order_by(EmailVerificationCode.created_at.desc())
        .first()
    )

    if not record:
        raise VerificationError("验证码无效或已过期")

    if _normalize_expires(record.expires_at) < _utcnow():
        raise VerificationError("验证码已过期，请重新获取")

    if record.attempt_count >= MAX_VERIFY_ATTEMPTS:
        raise VerificationError("验证码错误次数过多，请重新获取")

    if not verify_password(code, record.code_hash):
        record.attempt_count += 1
        db.commit()
        raise VerificationError("验证码错误")

    record.used_at = _utcnow()
    db.commit()
