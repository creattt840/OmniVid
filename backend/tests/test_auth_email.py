"""邮箱验证码认证相关单元测试。"""
import time
from datetime import datetime, timedelta, timezone

from app.db.models import EmailVerificationCode
from tests.conftest import get_last_code, register_user


def _send_code(client, email: str, purpose: str):
    return client.post("/api/auth/send-code", json={"email": email, "purpose": purpose})


def test_send_code_register_success(client):
    res = _send_code(client, "newuser@example.com", "register")
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert len(get_last_code()) == 6


def test_send_code_register_existing_email(client):
    register_user(client, "exists@example.com")
    res = _send_code(client, "exists@example.com", "register")
    assert res.status_code == 400
    assert "已注册" in res.json()["detail"]["error"]


def test_register_with_code(client):
    data = register_user(client, "reg@example.com")
    assert "token" in data


def test_register_duplicate_fails(client):
    register_user(client, "dup@example.com")
    _send_code(client, "dup@example.com", "register")
    res = client.post(
        "/api/auth/register",
        json={"email": "dup@example.com", "password": "test1234", "code": get_last_code()},
    )
    assert res.status_code == 400


def test_login_with_password(client):
    register_user(client, "pwd@example.com")
    res = client.post(
        "/api/auth/login",
        json={"email": "pwd@example.com", "password": "test1234"},
    )
    assert res.status_code == 200
    assert "token" in res.json()["data"]


def test_login_with_code(client):
    register_user(client, "code_login@example.com")
    _send_code(client, "code_login@example.com", "login")
    res = client.post(
        "/api/auth/login",
        json={"email": "code_login@example.com", "code": get_last_code()},
    )
    assert res.status_code == 200
    assert "token" in res.json()["data"]


def test_reset_password(client):
    register_user(client, "reset@example.com", "oldpass1")
    _send_code(client, "reset@example.com", "reset_password")
    res = client.post(
        "/api/auth/reset-password",
        json={
            "email": "reset@example.com",
            "code": get_last_code(),
            "new_password": "newpass2",
        },
    )
    assert res.status_code == 200

    old_login = client.post(
        "/api/auth/login",
        json={"email": "reset@example.com", "password": "oldpass1"},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/auth/login",
        json={"email": "reset@example.com", "password": "newpass2"},
    )
    assert new_login.status_code == 200


def test_send_code_login_unregistered(client):
    res = _send_code(client, "nobody@example.com", "login")
    assert res.status_code == 400
    assert "尚未注册" in res.json()["detail"]["error"]


def test_wrong_code_attempts(client):
    _send_code(client, "wrong@example.com", "register")
    for _ in range(5):
        res = client.post(
            "/api/auth/register",
            json={"email": "wrong@example.com", "password": "test1234", "code": "000000"},
        )
        assert res.status_code == 400

    res = client.post(
        "/api/auth/register",
        json={"email": "wrong@example.com", "password": "test1234", "code": get_last_code()},
    )
    assert res.status_code == 400
    assert "重新获取" in res.json()["detail"]["error"]


def test_resend_rate_limit(client):
    _send_code(client, "rate@example.com", "register")
    res = _send_code(client, "rate@example.com", "register")
    assert res.status_code == 429
    assert "秒" in res.json()["detail"]["error"]
    time.sleep(1.1)
    res2 = _send_code(client, "rate@example.com", "register")
    assert res2.status_code == 200


def test_expired_code_rejected(client):
    _send_code(client, "expired@example.com", "register")
    code = get_last_code()

    from app.db.connection import SessionLocal

    db = SessionLocal()
    record = (
        db.query(EmailVerificationCode)
        .filter(EmailVerificationCode.email == "expired@example.com")
        .first()
    )
    record.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()
    db.close()

    res = client.post(
        "/api/auth/register",
        json={"email": "expired@example.com", "password": "test1234", "code": code},
    )
    assert res.status_code == 400
    assert "过期" in res.json()["detail"]["error"]
