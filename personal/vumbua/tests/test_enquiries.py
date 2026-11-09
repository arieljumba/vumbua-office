import sqlite3
import smtplib

from app.services import mail


VALID_ENQUIRY = {
    "full_name": "Amina Wanjiku",
    "email": "amina@example.com",
    "phone": "+254 700 123 456",
    "occupation": "Operations analyst",
    "experience_level": "Some reporting/Excel experience",
    "learning_format": "Online",
    "enquiry_type": "Individual program",
    "reason": "I want to move from recurring spreadsheets into analytics.",
}


def test_valid_enquiry_is_saved(client, app):
    response = client.post("/contact", data=VALID_ENQUIRY)

    assert response.status_code == 303
    assert response.headers["Location"].endswith("/contact#enquiry")
    with sqlite3.connect(app.config["DATABASE_PATH"]) as connection:
        row = connection.execute(
            "SELECT full_name, email, experience_level, enquiry_type FROM enquiries"
        ).fetchone()
    assert row == (
        "Amina Wanjiku",
        "amina@example.com",
        "Some reporting/Excel experience",
        "Individual program",
    )


def test_invalid_enquiry_is_not_saved(client, app):
    response = client.post("/contact", data={**VALID_ENQUIRY, "email": "not-an-email"})

    assert response.status_code == 422
    assert b"Enter a valid email address." in response.data
    with sqlite3.connect(app.config["DATABASE_PATH"]) as connection:
        assert connection.execute("SELECT COUNT(*) FROM enquiries").fetchone()[0] == 0


def test_corporate_enquiry_type_is_supported(client, app):
    response = client.post(
        "/contact",
        data={**VALID_ENQUIRY, "enquiry_type": "Corporate team training"},
    )

    assert response.status_code == 303
    with sqlite3.connect(app.config["DATABASE_PATH"]) as connection:
        assert connection.execute(
            "SELECT enquiry_type FROM enquiries"
        ).fetchone()[0] == "Corporate team training"


def test_valid_enquiry_is_emailed_to_vumbua(client, app, monkeypatch):
    app.config.update(
        MAIL_SUPPRESS_SEND=False,
        MAIL_SMTP_HOST="smtp.example.com",
        MAIL_SMTP_USERNAME="info@vumbua.co.ke",
        MAIL_SMTP_PASSWORD="test-password",
    )
    sent_messages = []

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            assert (host, port, timeout) == ("smtp.example.com", 587, 10)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def ehlo(self):
            pass

        def starttls(self, context):
            pass

        def login(self, username, password):
            assert (username, password) == ("info@vumbua.co.ke", "test-password")

        def send_message(self, message):
            sent_messages.append(message)

    monkeypatch.setattr(mail.smtplib, "SMTP", FakeSMTP)

    response = client.post("/contact", data=VALID_ENQUIRY, follow_redirects=True)

    assert response.status_code == 200
    assert b"Your enquiry has been sent to Vumbua" in response.data
    assert len(sent_messages) == 1
    sent_message = sent_messages[0]
    assert sent_message["To"] == "info@vumbua.co.ke"
    assert sent_message["Reply-To"] == "amina@example.com"
    assert "Amina Wanjiku" in sent_message.get_content()
    assert VALID_ENQUIRY["reason"] in sent_message.get_content()


def test_smtp_failure_is_reported_and_enquiry_remains_saved(client, app, monkeypatch):
    app.config.update(
        MAIL_SUPPRESS_SEND=False,
        MAIL_SMTP_HOST="smtp.example.com",
    )

    def fail_to_connect(*args, **kwargs):
        raise smtplib.SMTPException("SMTP unavailable")

    monkeypatch.setattr(mail.smtplib, "SMTP", fail_to_connect)
    response = client.post("/contact", data=VALID_ENQUIRY, follow_redirects=True)

    assert response.status_code == 200
    assert b"flash-error" in response.data
    assert b"email Vumbua just now" in response.data
    assert b"Please contact us directly" in response.data
    with sqlite3.connect(app.config["DATABASE_PATH"]) as connection:
        assert connection.execute("SELECT COUNT(*) FROM enquiries").fetchone()[0] == 1


def test_missing_smtp_configuration_is_reported(client, app):
    app.config["MAIL_SUPPRESS_SEND"] = False

    response = client.post("/contact", data=VALID_ENQUIRY, follow_redirects=True)

    assert response.status_code == 200
    assert b"flash-error" in response.data
    assert b"email Vumbua just now" in response.data
    with sqlite3.connect(app.config["DATABASE_PATH"]) as connection:
        assert connection.execute("SELECT COUNT(*) FROM enquiries").fetchone()[0] == 1
