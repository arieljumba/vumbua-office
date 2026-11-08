from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from ..database import save_enquiry
from ..models import ENQUIRY_TYPES, EXPERIENCE_LEVELS, LEARNING_FORMATS, Enquiry

bp = Blueprint("enquiries", __name__)


@bp.get("/contact")
def contact():
    return render_template(
        "contact.html",
        page="contact",
        errors={},
        experience_levels=EXPERIENCE_LEVELS,
        learning_formats=LEARNING_FORMATS,
        enquiry_types=ENQUIRY_TYPES,
    )


@bp.post("/contact")
def submit_enquiry():
    enquiry, errors = Enquiry.from_form(request.form)
    if errors:
        current_app.logger.info("Rejected invalid enquiry form (%s fields)", len(errors))
        return (
            render_template(
                "contact.html",
                page="contact",
                errors=errors,
                experience_levels=EXPERIENCE_LEVELS,
                learning_formats=LEARNING_FORMATS,
                enquiry_types=ENQUIRY_TYPES,
            ),
            422,
        )

    try:
        save_enquiry(
            {
                "full_name": enquiry.full_name,
                "email": enquiry.email,
                "phone": enquiry.phone,
                "occupation": enquiry.occupation,
                "experience_level": enquiry.experience_level,
                "learning_format": enquiry.learning_format,
                "enquiry_type": enquiry.enquiry_type,
                "reason": enquiry.reason,
            },
            datetime.now(timezone.utc).isoformat(),
        )
    except Exception:
        current_app.logger.exception("Could not save an enquiry")
        return (
            render_template(
                "error.html",
                code=500,
                title="Your enquiry wasn't sent",
                message="We couldn't save your details. Please try again in a moment.",
            ),
            500,
        )

    flash("Thanks for getting in touch. Your enquiry has been received.", "success")
    return redirect(url_for("enquiries.contact") + "#enquiry", code=303)
