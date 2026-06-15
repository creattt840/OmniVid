import os
import time

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from deps import get_current_user
from membership import VIP_DURATION_DAYS, extend_vip
from models import Membership, StripeEvent, User

router = APIRouter(prefix="/api/billing", tags=["billing"])

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


@router.post("/checkout")
def create_checkout(user: User = Depends(get_current_user)):
    if not STRIPE_SECRET_KEY or not STRIPE_PRICE_ID:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "支付服务未配置，请联系管理员设置 STRIPE_SECRET_KEY 和 STRIPE_PRICE_ID",
                "code": "STRIPE_NOT_CONFIGURED",
            },
        )
    # 5 分钟窗口内同一用户重复点击返回同一 session（Stripe 幂等）
    bucket = int(time.time()) // 300
    idempotency_key = f"checkout-{user.id}-{bucket}"
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
            client_reference_id=str(user.id),
            metadata={"user_id": str(user.id)},
            success_url=f"{FRONTEND_URL}/?checkout=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/?checkout=cancel",
            idempotency_key=idempotency_key,
        )
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=502,
            detail={"success": False, "error": f"创建支付会话失败: {e.user_message or str(e)}"},
        )
    return {
        "success": True,
        "data": {
            "checkout_url": session.url,
            "session_id": session.id,
        },
    }


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
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook 未配置")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
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
