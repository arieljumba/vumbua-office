import sqlite3


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
