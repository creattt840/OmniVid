import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dependencies import get_current_user
from app.db.connection import get_db
from app.db.models import Membership, StripeEvent, User
from app.services.membership import VIP_DURATION_DAYS, extend_vip

router = APIRouter(prefix="/api/billing", tags=["billing"])

_settings = get_settings()
if _settings.stripe_secret_key:
    stripe.api_key = _settings.stripe_secret_key


@router.post("/checkout")
def create_checkout(user: User = Depends(get_current_user)):
    raise HTTPException(
        status_code=503,
        detail={
            "success": False,
            "error": "会员功能暂未开放，敬请期待",
            "code": "MEMBERSHIP_DISABLED",
        },
    )


def _as_dict(obj) -> dict:
    """Stripe Webhook 的 object 是 StripeObject，不是 dict。"""
    if isinstance(obj, dict):
        return obj
    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    return dict(obj)


def _resolve_user_id(session: dict) -> int | None:
    metadata = session.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = _as_dict(metadata)
    user_id = metadata.get("user_id")
    if user_id:
        return int(user_id)
    ref = session.get("client_reference_id")
    if ref:
        return int(ref)
    return None


def _handle_checkout_completed(db: Session, session_obj) -> None:
    session = _as_dict(session_obj)
    if session.get("payment_status") != "paid":
        return
    user_id = _resolve_user_id(session)
    if not user_id:
        raise ValueError("checkout session 缺少 user_id")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"用户不存在: {user_id}")

    session_id = session.get("id")
    existing = (
        db.query(Membership)
        .filter(Membership.stripe_checkout_session_id == session_id)
        .first()
    )
    if existing:
        return

    amount = session.get("amount_total") or 0
    currency = session.get("currency") or "cny"
    db.add(
        Membership(
            user_id=user.id,
            stripe_checkout_session_id=session_id,
            amount_cents=amount,
            currency=currency,
        )
    )
    extend_vip(db, user, VIP_DURATION_DAYS, commit=False)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    if not _settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook 未配置")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, _settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    existing_event = (
        db.query(StripeEvent).filter(StripeEvent.event_id == event["id"]).first()
    )
    if existing_event:
        return {"status": "already_processed"}

    try:
        if event["type"] == "checkout.session.completed":
            _handle_checkout_completed(db, event["data"]["object"])
        db.add(
            StripeEvent(
                event_id=event["id"],
                event_type=event["type"],
            )
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"status": "already_processed"}
    except Exception:
        db.rollback()
        raise

    return {"status": "ok"}
