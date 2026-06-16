import importlib
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET", "test-secret-key")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test")
os.environ.setdefault("SMTP_USER", "test@example.com")
os.environ.setdefault("SMTP_PASSWORD", "test-smtp-password")
os.environ.setdefault("SMTP_FROM", "test@example.com")
os.environ.setdefault("VERIFY_CODE_RESEND_SECONDS", "1")

_last_sent_code: dict = {}


@pytest.fixture(autouse=True)
def mock_email_send(monkeypatch):
    def fake_send(to_email: str, code: str, purpose: str) -> None:
        _last_sent_code.clear()
        _last_sent_code.update({"email": to_email, "code": code, "purpose": purpose})

    monkeypatch.setattr(
        "app.services.verification.send_verification_email",
        fake_send,
    )


def get_last_code() -> str:
    return _last_sent_code["code"]


def register_user(client, email: str, password: str = "test1234") -> dict:
    res = client.post(
        "/api/auth/send-code",
        json={"email": email, "purpose": "register"},
    )
    assert res.status_code == 200, res.text
    res = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "code": get_last_code()},
    )
    assert res.status_code == 200, res.text
    return res.json()["data"]


def register_and_login(client, email: str, password: str = "test1234") -> dict:
    data = register_user(client, email, password)
    token = data["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def client(request):
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.replace(chr(92), '/')}"

    from app.core.config import get_settings

    get_settings.cache_clear()

    import app.db.connection as db_connection
    import app.services.membership as membership_module

    importlib.reload(db_connection)
    importlib.reload(membership_module)

    from main import app

    db_connection.init_db()
    with TestClient(app) as test_client:
        yield test_client

    db_connection.engine.dispose()
    try:
        os.remove(db_path)
    except OSError:
        pass
