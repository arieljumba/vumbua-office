from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Enquiry:
    full_name: str
    email: str
    phone: str
    occupation: str
    experience_level: str
    learning_format: str
    enquiry_type: str
    reason: str

    @classmethod
    def from_form(cls, form) -> tuple[Enquiry | None, dict[str, str]]:
        values = {
            "full_name": _clean(form.get("full_name")),
            "email": _clean(form.get("email")).lower(),
            "phone": _clean(form.get("phone")),
            "occupation": _clean(form.get("occupation")),
            "experience_level": _clean(form.get("experience_level")),
            "learning_format": _clean(form.get("learning_format")),
            "enquiry_type": _clean(form.get("enquiry_type")),
            "reason": _clean(form.get("reason")),
        }
        errors: dict[str, str] = {}

        if not 2 <= len(values["full_name"]) <= 120:
            errors["full_name"] = "Enter your name (2 to 120 characters)."
        if len(values["email"]) > 254:
            errors["email"] = "Enter a valid email address."
        else:
            from email_validator import EmailNotValidError, validate_email

            try:
                validate_email(values["email"], check_deliverability=False)
            except EmailNotValidError:
                errors["email"] = "Enter a valid email address."

        phone_digits = sum(character.isdigit() for character in values["phone"])
        if (
            not 7 <= phone_digits <= 15
            or len(values["phone"]) > 30
            or not re.fullmatch(r"[0-9+().\-\s]+", values["phone"])
        ):
            errors["phone"] = "Enter a phone number with 7 to 15 digits."
        if not 2 <= len(values["occupation"]) <= 120:
            errors["occupation"] = "Tell us your current occupation."
        if values["experience_level"] not in EXPERIENCE_LEVELS:
            errors["experience_level"] = "Choose an experience level."
        if values["learning_format"] not in LEARNING_FORMATS:
            errors["learning_format"] = "Choose a learning format."
        if values["enquiry_type"] not in ENQUIRY_TYPES:
            errors["enquiry_type"] = "Choose what you are enquiring about."
        if not 10 <= len(values["reason"]) <= 2000:
            errors["reason"] = "Please share a little more (10 to 2,000 characters)."

        if errors:
            return None, errors
        return cls(**values), {}


EXPERIENCE_LEVELS = (
    "Beginner",
    "Some reporting/Excel experience",
    "Some analytics experience",
    "Working in data",
)

LEARNING_FORMATS = ("Online", "In person", "Hybrid", "Discuss with me")
ENQUIRY_TYPES = ("Individual program", "Corporate team training")


def _clean(value: str | None) -> str:
    return (value or "").strip()
