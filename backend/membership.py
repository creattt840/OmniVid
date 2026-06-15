import os
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from models import UsageDaily, User

FREE_DAILY_AI_LIMIT = int(os.getenv("FREE_DAILY_AI_LIMIT", "10"))
VIP_DURATION_DAYS = int(os.getenv("VIP_DURATION_DAYS", "30"))
AI_ANALYZE_ACTION = "ai_analyze"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_dt(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def user_is_vip(user: User) -> bool:
    return user.is_vip


def get_today_ai_usage(db: Session, user_id: int) -> int:
    today = date.today()
    record = (
        db.query(UsageDaily)
        .filter(
            UsageDaily.user_id == user_id,
            UsageDaily.action == AI_ANALYZE_ACTION,
            UsageDaily.usage_date == today,
        )
        .first()
    )
    return record.count if record else 0


def check_ai_quota(db: Session, user: User) -> tuple[bool, str | None]:
    """返回 (allowed, error_message)。"""
    used = get_today_ai_usage(db, user.id)
    if used >= FREE_DAILY_AI_LIMIT:
        return False, f"每日 AI 分析限 {FREE_DAILY_AI_LIMIT} 次，今日已用完，请明天再试。"
    return True, None


def consume_ai_quota(db: Session, user: User) -> None:
    today = date.today()
    record = (
        db.query(UsageDaily)
        .filter(
            UsageDaily.user_id == user.id,
            UsageDaily.action == AI_ANALYZE_ACTION,
            UsageDaily.usage_date == today,
        )
        .first()
    )
    if record:
        record.count += 1
    else:
        db.add(
            UsageDaily(
                user_id=user.id,
                action=AI_ANALYZE_ACTION,
                usage_date=today,
                count=1,
            )
        )
    db.commit()


def extend_vip(db: Session, user: User, days: int = VIP_DURATION_DAYS, *, commit: bool = True) -> datetime:
    now = _utcnow()
    current = _normalize_dt(user.vip_expires_at)
    base = current if current and current > now else now
    new_expires = base + timedelta(days=days)
    user.vip_expires_at = new_expires
    if commit:
        db.commit()
        db.refresh(user)
    return new_expires


def serialize_user(db: Session, user: User) -> dict:
    vip_expires = _normalize_dt(user.vip_expires_at)
    return {
        "id": user.id,
        "email": user.email,
        "is_vip": user_is_vip(user),
        "vip_expires_at": vip_expires.isoformat() if vip_expires else None,
        "ai_usage_today": get_today_ai_usage(db, user.id),
        "ai_daily_limit": FREE_DAILY_AI_LIMIT,
        "membership_enabled": False,
    }
