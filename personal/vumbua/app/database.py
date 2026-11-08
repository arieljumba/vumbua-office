from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from flask import current_app


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(
        current_app.config["DATABASE_PATH"],
        timeout=10,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


@contextmanager
def connection_scope() -> Generator[sqlite3.Connection, None, None]:
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db() -> None:
    database_path = Path(current_app.config["DATABASE_PATH"])
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with connection_scope() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS enquiries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                occupation TEXT NOT NULL,
                experience_level TEXT NOT NULL,
                learning_format TEXT NOT NULL,
                enquiry_type TEXT NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def save_enquiry(enquiry: dict[str, str], created_at: str) -> int:
    with connection_scope() as connection:
        cursor = connection.execute(
            """
            INSERT INTO enquiries (
                full_name, email, phone, occupation, experience_level,
                learning_format, enquiry_type, reason, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                enquiry["full_name"],
                enquiry["email"],
                enquiry["phone"],
                enquiry["occupation"],
                enquiry["experience_level"],
                enquiry["learning_format"],
                enquiry["enquiry_type"],
                enquiry["reason"],
                created_at,
            ),
        )
        return int(cursor.lastrowid)
