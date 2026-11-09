from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    ENVIRONMENT = os.getenv("FLASK_ENV", "development").lower()
    DEVELOPMENT_SECRET = "local-development-key-change-before-deploying"
    SECRET_KEY = os.getenv("SECRET_KEY") or (
        DEVELOPMENT_SECRET if ENVIRONMENT != "production" else ""
    )
    DATABASE_PATH = os.getenv("DATABASE_PATH") or "instance/vumbua.sqlite3"
    MARKET_DATA_FILE = os.getenv("MARKET_DATA_FILE") or "instance/market_roles.csv"
    MARKET_DATA_SOURCE_URL = os.getenv("MARKET_DATA_SOURCE_URL", "")
    MARKET_DATA_SOURCE_FORMAT = (
        os.getenv("MARKET_DATA_SOURCE_FORMAT") or "csv"
    ).lower()
    MARKET_DATA_TABLE_INDEX = int(os.getenv("MARKET_DATA_TABLE_INDEX", "0"))
    MAIL_SMTP_HOST = os.getenv("MAIL_SMTP_HOST", "")
    MAIL_SMTP_PORT = int(os.getenv("MAIL_SMTP_PORT", "587"))
    MAIL_SMTP_USERNAME = os.getenv("MAIL_SMTP_USERNAME", "")
    MAIL_SMTP_PASSWORD = os.getenv("MAIL_SMTP_PASSWORD", "")
    MAIL_FROM_ADDRESS = os.getenv("MAIL_FROM_ADDRESS", "info@vumbua.co.ke")
    MAIL_TO_ADDRESS = os.getenv("MAIL_TO_ADDRESS", "info@vumbua.co.ke")
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    MAIL_USE_STARTTLS = os.getenv("MAIL_USE_STARTTLS", "true").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    MAIL_TIMEOUT = float(os.getenv("MAIL_TIMEOUT", "10"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "")
    MAX_CONTENT_LENGTH = 16 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = ENVIRONMENT == "production"
    PREFERRED_URL_SCHEME = "https" if ENVIRONMENT == "production" else "http"
