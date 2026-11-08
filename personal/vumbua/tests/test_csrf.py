from app import create_app
import pytest


def test_contact_rejects_missing_csrf_token(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "ENVIRONMENT": "testing",
            "SECRET_KEY": "test-secret",
            "WTF_CSRF_ENABLED": True,
            "DATABASE_PATH": str(tmp_path / "csrf.sqlite3"),
            "MARKET_DATA_FILE": str(tmp_path / "market_roles.csv"),
        }
    )

    response = app.test_client().post("/contact", data={"full_name": "A user"})

    assert response.status_code == 400
    assert b"reload the form" in response.data


def test_production_requires_a_long_secret_key(tmp_path):
    with pytest.raises(RuntimeError, match="at least 32 characters"):
        create_app(
            {
                "TESTING": True,
                "ENVIRONMENT": "production",
                "SECRET_KEY": "",
                "DATABASE_PATH": str(tmp_path / "production.sqlite3"),
                "MARKET_DATA_FILE": str(tmp_path / "market_roles.csv"),
            }
        )
