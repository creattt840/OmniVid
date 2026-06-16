"""会员与支付相关单元测试。"""
import json
import os
from datetime import datetime, timedelta, timezone

import pytest

from tests.conftest import register_and_login

os.environ["FREE_DAILY_AI_LIMIT"] = "10"


def _register_and_login(client, email: str, password: str = "test1234"):
    return register_and_login(client, email, password)


def test_register_login_me(client):
    headers = _register_and_login(client, "user1@example.com")
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    data = me.json()["data"]
    assert data["email"] == "user1@example.com"
    assert data["is_vip"] is False
    assert data["ai_daily_limit"] == 10
    assert data["membership_enabled"] is False


def test_ai_quota_enforcement(client):
    from app.db.connection import SessionLocal
    from app.db.models import User
    from app.services.membership import check_ai_quota, consume_ai_quota

    headers = _register_and_login(client, "quota@example.com")
    db = SessionLocal()
    user = db.query(User).filter(User.email == "quota@example.com").first()
    for _ in range(10):
        consume_ai_quota(db, user)
    allowed, msg = check_ai_quota(db, user)
    assert allowed is False
    assert "10" in msg
    db.close()


def test_vip_still_has_daily_quota(client):
    """VIP 状态不再绕过每日配额。"""
    from app.db.connection import SessionLocal
    from app.db.models import User
    from app.services.membership import check_ai_quota, consume_ai_quota

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


def test_vip_extend_stacking(client):
    from app.db.connection import SessionLocal
    from app.db.models import User
    from app.services.membership import extend_vip

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


def test_webhook_idempotency(client, monkeypatch):
    """同一 event_id 处理两次，VIP 只延长一次。"""
    import stripe

    headers = _register_and_login(client, "webhook@example.com")
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

    from app.db.connection import SessionLocal
    from app.db.models import Membership

    db = SessionLocal()
    count = db.query(Membership).filter(Membership.user_id == user_id).count()
    assert count == 1
    db.close()


def test_checkout_requires_auth(client):
    res = client.post("/api/billing/checkout")
    assert res.status_code == 401


def test_checkout_disabled_when_logged_in(client):
    headers = _register_and_login(client, "checkout_disabled@example.com")
    res = client.post("/api/billing/checkout", headers=headers)
    assert res.status_code == 503
    detail = res.json()["detail"]
    assert detail["code"] == "MEMBERSHIP_DISABLED"
