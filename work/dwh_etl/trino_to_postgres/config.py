import os
from dataclasses import dataclass

from trino.auth import BasicAuthentication

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


@dataclass
class Settings:
    remote_host: str
    remote_port: str
    remote_user: str
    remote_catalog: str
    remote_schema: str
    remote_http_scheme: str
    remote_verify_tls: bool

    local_host: str
    local_port: str
    local_db: str
    local_schema: str
    local_user: str
    local_password: str
    remote_password: str

    @property
    def remote_db_url(self) -> str:
        return (
            f"trino://{self.remote_user}@{self.remote_host}"
            f":{self.remote_port}/{self.remote_catalog}/{self.remote_schema}"
        )

    @property
    def remote_connect_args(self) -> dict:
        return {
            "http_scheme": self.remote_http_scheme,
            "verify": self.remote_verify_tls,
            "auth": BasicAuthentication(self.remote_user, self.remote_password),
        }

    @property
    def local_db_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.local_user}:{self.local_password}"
            f"@{self.local_host}:{self.local_port}/{self.local_db}"
        )


def _require(key: str) -> str:
    val = os.getenv(key, "").strip()
    if not val:
        raise ValueError(f"Missing {key} in environment or .env file")
    return val


def _parse_bool_env(key: str, default: bool = True) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    val = raw.strip().lower()
    if val in {"1", "true", "yes", "y", "on"}:
        return True
    if val in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"{key} must be a boolean value")


def load_settings() -> Settings:
    if load_dotenv:
        load_dotenv()

    remote_port = os.getenv("REMOTE_PORT", "8080").strip()
    remote_http_scheme = os.getenv("REMOTE_HTTP_SCHEME", "").strip().lower()
    if not remote_http_scheme:
        remote_http_scheme = "https" if remote_port == "8443" else "http"
    if remote_http_scheme not in {"http", "https"}:
        raise ValueError("REMOTE_HTTP_SCHEME must be either 'http' or 'https'")
    remote_verify_tls = _parse_bool_env("REMOTE_VERIFY_TLS", default=True)

    local_password = os.getenv("LOCAL_PASS", "").strip() or os.getenv(
        "LOCAL_PASSWORD", ""
    ).strip()
    if not local_password:
        raise ValueError("Missing LOCAL_PASS (or LOCAL_PASSWORD) in environment or .env file")

    return Settings(
        remote_host=_require("REMOTE_HOST"),
        remote_port=remote_port,
        remote_user=_require("REMOTE_USER"),
        remote_catalog=_require("REMOTE_CATALOG"),
        remote_schema=_require("REMOTE_SCHEMA"),
        remote_http_scheme=remote_http_scheme,
        remote_verify_tls=remote_verify_tls,
        remote_password=_require("REMOTE_PASS"),
        local_host=os.getenv("LOCAL_HOST", "localhost").strip(),
        local_port=os.getenv("LOCAL_PORT", "5432").strip(),
        local_db=_require("LOCAL_DB"),
        local_schema=os.getenv("LOCAL_SCHEMA", "hfcb").strip(),
        local_user=_require("LOCAL_USER"),
        local_password=local_password,
    )
