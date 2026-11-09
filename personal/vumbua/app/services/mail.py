from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

from flask import current_app

from ..models import Enquiry


class EmailDeliveryError(Exception):
    """Raised when an enquiry cannot be delivered by email."""


def send_enquiry_email(enquiry: Enquiry) -> None:
    config = current_app.config
    if current_app.testing and config.get("MAIL_SUPPRESS_SEND"):
        return

    host = config["MAIL_SMTP_HOST"]
    username = config["MAIL_SMTP_USERNAME"]
    password = config["MAIL_SMTP_PASSWORD"]

    if not host:
        raise EmailDeliveryError("MAIL_SMTP_HOST is not configured.")
    if bool(username) != bool(password):
        raise EmailDeliveryError(
            "Both MAIL_SMTP_USERNAME and MAIL_SMTP_PASSWORD must be configured."
        )
    if config["MAIL_USE_SSL"] and config["MAIL_USE_STARTTLS"]:
        raise EmailDeliveryError(
            "MAIL_USE_SSL and MAIL_USE_STARTTLS cannot both be enabled."
        )

    message = EmailMessage()
    message["Subject"] = f"New Vumbua website enquiry: {enquiry.enquiry_type}"
    message["From"] = config["MAIL_FROM_ADDRESS"]
    message["To"] = config["MAIL_TO_ADDRESS"]
    message["Reply-To"] = enquiry.email
    message.set_content(
        "\n".join(
            (
                "A new enquiry was submitted on the Vumbua website.",
                "",
                f"Name: {enquiry.full_name}",
                f"Email: {enquiry.email}",
                f"Phone: {enquiry.phone}",
                f"Occupation: {enquiry.occupation}",
                f"Experience level: {enquiry.experience_level}",
                f"Learning format: {enquiry.learning_format}",
                f"Enquiry type: {enquiry.enquiry_type}",
                "",
                "What they would like to learn or solve:",
                enquiry.reason,
            )
        )
    )

    try:
        smtp_client = (
            smtplib.SMTP_SSL if config["MAIL_USE_SSL"] else smtplib.SMTP
        )
        smtp_options = (
            {"context": ssl.create_default_context()} if config["MAIL_USE_SSL"] else {}
        )
        with smtp_client(
            host,
            config["MAIL_SMTP_PORT"],
            timeout=config["MAIL_TIMEOUT"],
            **smtp_options,
        ) as server:
            server.ehlo()
            if not config["MAIL_USE_SSL"] and config["MAIL_USE_STARTTLS"]:
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
            if username:
                server.login(username, password)
            server.send_message(message)
    except (OSError, smtplib.SMTPException) as error:
        raise EmailDeliveryError("The SMTP server could not deliver the enquiry.") from error
