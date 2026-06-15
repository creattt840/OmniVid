"""会员与支付相关单元测试。"""
import json
import os
import time
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_omnivid.db")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test")
os.environ["FREE_DAILY_AI_LIMIT"] = "10"

# 清理旧测试库
test_db = os.path.join(os.path.dirname(__file__), "test_omnivid.db")
if os.path.exists(test_db):
    os.remove(test_db)

from main import app  # noqa: E402
from database import SessionLocal, init_db  # noqa: E402
from models import User  # noqa: E402
from membership import extend_vip, get_today_ai_usage, check_ai_quota, consume_ai_quota  # noqa: E402

init_db()
client = TestClient(app)


def _register_and_login(email: str, password: str = "test1234"):
    client.post("/api/auth/register", json={"email": email, "password": password})
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    token = res.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_login_me():
    headers = _register_and_login("user1@example.com")
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    data = me.json()["data"]
    assert data["email"] == "user1@example.com"
    assert data["is_vip"] is False
    assert data["ai_daily_limit"] == 10
    assert data["membership_enabled"] is False


def test_ai_quota_enforcement():
    headers = _register_and_login("quota@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "quota@example.com").first()
    for _ in range(10):
        consume_ai_quota(db, user)
    allowed, msg = check_ai_quota(db, user)
    assert allowed is False
    assert "10" in msg
    db.close()


def test_vip_still_has_daily_quota():
    """VIP 状态不再绕过每日配额。"""
    db = SessionLocal()
    user = User(email="vip_quota@example.com", password_hash="x")
    user.vip_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    db.add(user)
    db.commit()
    db.refresh(user)
    for _ in range(10):
        consume_ai_quota(db, user)
    allowed, _ = check_ai_quota(db, user)
    assert allowed is False
    db.close()


def test_vip_extend_stacking():
    db = SessionLocal()
    user = User(email="vip@example.com", password_hash="x")
    db.add(user)
    db.commit()
    db.refresh(user)
    future = datetime.now(timezone.utc) + timedelta(days=10)
    user.vip_expires_at = future
    db.commit()
    new_expires = extend_vip(db, user, days=30)
    assert new_expires > future
    db.close()


def test_webhook_idempotency(monkeypatch):
    """同一 event_id 处理两次，VIP 只延长一次。"""
    import billing as billing_mod
    import stripe

    headers = _register_and_login("webhook@example.com")
    me = client.get("/api/auth/me", headers=headers)
    user_id = me.json()["data"]["id"]

    session_data = {
        "id": "cs_test_123",
        "payment_status": "paid",
        "amount_total": 990,
        "currency": "cny",
        "metadata": {"user_id": str(user_id)},
    }
    event = {
        "id": "evt_test_idempotent_001",
        "type": "checkout.session.completed",
        "data": {"object": session_data},
    }

    def fake_construct(payload, sig, secret):
        return event

    monkeypatch.setattr(stripe.Webhook, "construct_event", fake_construct)

    for _ in range(2):
        res = client.post(
            "/api/billing/webhook",
            data=json.dumps(event),
            headers={"stripe-signature": "t=1,v1=fake"},
        )
        assert res.status_code == 200

    me2 = client.get("/api/auth/me", headers=headers)
    assert me2.json()["data"]["is_vip"] is True

    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    from models import Membership
    count = db.query(Membership).filter(Membership.user_id == user_id).count()
    assert count == 1
    db.close()


def test_checkout_requires_auth():
    res = client.post("/api/billing/checkout")
    assert res.status_code == 401


def test_checkout_disabled_when_logged_in():
    headers = _register_and_login("checkout_disabled@example.com")
    res = client.post("/api/billing/checkout", headers=headers)
    assert res.status_code == 503
    detail = res.json()["detail"]
    assert detail["code"] == "MEMBERSHIP_DISABLED"
