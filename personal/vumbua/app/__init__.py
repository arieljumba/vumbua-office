from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import click
from datetime import datetime, timezone

from flask import Flask, render_template
from flask_wtf.csrf import CSRFError, CSRFProtect

from .config import Config
from .database import init_db
from .market_data.service import refresh_market_data
from .routes import enquiries, insights, pages

csrf = CSRFProtect()


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    for key in ("DATABASE_PATH", "MARKET_DATA_FILE"):
        configured_path = Path(app.config[key])
        if not configured_path.is_absolute():
            app.config[key] = str((Path(app.root_path).parent / configured_path).resolve())

    if app.config["ENVIRONMENT"] == "production" and (
        len(app.config["SECRET_KEY"]) < 32
        or app.config["SECRET_KEY"] == Config.DEVELOPMENT_SECRET
    ):
        raise RuntimeError(
            "Set a unique SECRET_KEY of at least 32 characters before running in production."
        )

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["DATABASE_PATH"]).parent.mkdir(parents=True, exist_ok=True)
    Path(app.config["MARKET_DATA_FILE"]).parent.mkdir(parents=True, exist_ok=True)
    _configure_logging(app)

    csrf.init_app(app)
    app.register_blueprint(pages.bp)
    app.register_blueprint(insights.bp)
    app.register_blueprint(enquiries.bp)

    @app.context_processor
    def inject_current_year():
        return {"current_year": datetime.now(timezone.utc).year}

    with app.app_context():
        init_db()

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self' https://cdn.plot.ly; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'",
        )
        if app.config["ENVIRONMENT"] == "production":
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        app.logger.info("Rejected request with invalid CSRF token: %s", error.description)
        return render_template(
            "error.html",
            code=400,
            title="Please reload the form",
            message="This form has expired or could not be verified. Reload the page and try again.",
        ), 400

    @app.errorhandler(404)
    def not_found(error):
        app.logger.debug("Page not found: %s", error)
        return render_template(
            "error.html",
            code=404,
            title="This page isn't here",
            message="The page may have moved. Head back to the home page to find your way.",
        ), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.exception("Unhandled application error: %s", error)
        return render_template(
            "error.html",
            code=500,
            title="Something went wrong",
            message="We couldn't complete that request. Please try again shortly.",
        ), 500

    @app.cli.command("init-db")
    def init_db_command():
        """Create the local application database."""
        init_db()
        click.echo("Application database initialized.")

    @app.cli.command("refresh-market-data")
    @click.option(
        "--source",
        default=None,
        help="Local source file or HTTPS URL. Defaults to MARKET_DATA_SOURCE_URL.",
    )
    @click.option(
        "--format",
        "source_format",
        type=click.Choice(["csv", "json", "html"], case_sensitive=False),
        default=None,
        help="Source format. HTML uses a permitted page table with canonical column names.",
    )
    @click.option(
        "--table-index",
        type=click.IntRange(min=0),
        default=None,
        help="Zero-based HTML table index. Defaults to MARKET_DATA_TABLE_INDEX.",
    )
    def refresh_market_data_command(source, source_format, table_index):
        """Replace the market dataset using a configured, permitted public source."""
        source = source or app.config["MARKET_DATA_SOURCE_URL"]
        source_format = (source_format or app.config["MARKET_DATA_SOURCE_FORMAT"]).lower()
        table_index = (
            app.config["MARKET_DATA_TABLE_INDEX"] if table_index is None else table_index
        )
        if not source:
            raise click.ClickException(
                "No market data source configured. Set MARKET_DATA_SOURCE_URL or pass --source."
            )
        try:
            count = refresh_market_data(
                source,
                source_format,
                Path(app.config["MARKET_DATA_FILE"]),
                table_index=table_index,
            )
        except (OSError, ValueError) as error:
            app.logger.exception("Market data refresh failed")
            raise click.ClickException(str(error)) from error
        click.echo(f"Market dataset refreshed: {count} validated records.")

    return app


def _configure_logging(app: Flask) -> None:
    level = getattr(logging, str(app.config["LOG_LEVEL"]).upper(), logging.INFO)
    app.logger.setLevel(level)
    if not app.logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        app.logger.addHandler(handler)

    log_path = app.config.get("LOG_FILE")
    if log_path:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3)
        handler.setLevel(level)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        app.logger.addHandler(handler)
