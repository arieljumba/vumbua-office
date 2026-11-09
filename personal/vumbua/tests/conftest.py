from __future__ import annotations

import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "ENVIRONMENT": "testing",
            "SECRET_KEY": "test-secret",
            "WTF_CSRF_ENABLED": False,
            "DATABASE_PATH": str(tmp_path / "test.sqlite3"),
            "MARKET_DATA_FILE": str(tmp_path / "market_roles.csv"),
            "MAIL_SUPPRESS_SEND": True,
        }
    )


@pytest.fixture
def client(app):
    return app.test_client()
