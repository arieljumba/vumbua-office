from __future__ import annotations

from datetime import date

from flask import Blueprint, current_app, jsonify, render_template, request

from ..market_data.service import (
    dashboard_payload,
    filter_dataset,
    filter_options,
    get_dataset,
    source_details,
)

bp = Blueprint("insights", __name__)


@bp.get("/market-insights")
def market_insights():
    frame, metadata = get_dataset()
    options = filter_options(frame)
    return render_template(
        "insights.html",
        page="insights",
        metadata=metadata,
        options=options,
        sources=source_details(frame),
    )


@bp.get("/api/market-insights")
def market_insights_api():
    frame, metadata = get_dataset()
    filters = {
        key: request.args.get(key, "").strip()
        for key in ("location", "role", "skill", "experience", "start_date", "end_date")
    }
    for key in ("start_date", "end_date"):
        if filters[key]:
            try:
                date.fromisoformat(filters[key])
            except ValueError:
                return jsonify({"error": f"{key} must use YYYY-MM-DD format."}), 400
    if filters["start_date"] and filters["end_date"]:
        if filters["start_date"] > filters["end_date"]:
            return jsonify({"error": "start_date must be on or before end_date."}), 400
    if filters["location"] not in filter_options(frame)["locations"] and filters["location"]:
        return jsonify({"error": "Choose a location from the available filters."}), 400
    if filters["role"] not in filter_options(frame)["roles"] and filters["role"]:
        return jsonify({"error": "Choose a role from the available filters."}), 400
    if (
        filters["experience"]
        and filters["experience"] not in filter_options(frame)["experience"]
    ):
        return jsonify({"error": "Choose an experience level from the available filters."}), 400
    if filters["skill"] and filters["skill"] not in filter_options(frame)["skills"]:
        return jsonify({"error": "Choose a skill from the available filters."}), 400

    filtered = filter_dataset(frame, filters)
    payload = dashboard_payload(filtered)
    payload.update(
        {
            "metadata": metadata,
            "filters": filters,
            "filter_options": filter_options(frame),
            "sources": source_details(frame),
        }
    )
    current_app.logger.debug(
        "Served market insights with %s filters and %s rows",
        sum(bool(value) for value in filters.values()),
        len(filtered),
    )
    return jsonify(payload)
