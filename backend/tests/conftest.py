import importlib
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET", "test-secret-key")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test")


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
