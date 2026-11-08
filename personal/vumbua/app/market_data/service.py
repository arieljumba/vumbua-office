from __future__ import annotations

import io
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from flask import current_app

REQUIRED_COLUMNS = ("posted_at", "role", "location", "skills")
OPTIONAL_DEFAULTS = {
    "experience": "Not specified",
    "work_mode": "Not specified",
    "source": "Configured public source",
    "source_url": "",
}
MAX_SOURCE_BYTES = 25 * 1024 * 1024
DEMO_SOURCE_LABEL = "Bundled synthetic demonstration dataset"
DEMO_METHOD = (
    "Every row in this view is synthetic demonstration data created to show the "
    "analysis workflow. It is not a sample of current vacancies and should not be "
    "used to infer actual hiring demand. A live dataset requires a permitted, "
    "documented public source."
)


def get_dataset() -> tuple[pd.DataFrame, dict[str, str]]:
    data_path = Path(current_app.config["MARKET_DATA_FILE"])
    manifest_path = data_path.with_suffix(".json")
    if not data_path.exists():
        fallback_path = Path(__file__).resolve().parents[1] / "data" / "demo_market_roles.csv"
        frame = pd.read_csv(fallback_path)
        manifest = {
            "source": DEMO_SOURCE_LABEL,
            "updated_at": "2026-11-08T00:00:00+03:00",
            "methodology": DEMO_METHOD,
            "demo": "true",
        }
        return _normalize_frame(frame), manifest

    frame = pd.read_csv(data_path)
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = {
            "source": DEMO_SOURCE_LABEL,
            "updated_at": datetime.fromtimestamp(
                data_path.stat().st_mtime, tz=timezone.utc
            ).isoformat(),
            "methodology": DEMO_METHOD,
            "demo": "true",
        }
    return _normalize_frame(frame), manifest


def filter_dataset(frame: pd.DataFrame, filters: dict[str, str]) -> pd.DataFrame:
    result = frame.copy()
    for column in ("location", "role", "experience"):
        value = filters.get(column, "").strip()
        if value:
            result = result[result[column].str.casefold() == value.casefold()]

    skill = filters.get("skill", "").strip()
    if skill:
        result = result[result["skills"].str.contains(_literal_pattern(skill), case=False)]

    start_date = filters.get("start_date", "").strip()
    end_date = filters.get("end_date", "").strip()
    if start_date:
        result = result[result["posted_at"] >= pd.Timestamp(start_date)]
    if end_date:
        result = result[result["posted_at"] <= pd.Timestamp(end_date)]
    return result


def dashboard_payload(frame: pd.DataFrame) -> dict:
    rows = len(frame)
    skill_counts = _skill_counts(frame)
    top_skills = skill_counts.head(9).reset_index()
    top_skills.columns = ["skill", "opportunities"]

    by_month = (
        frame.set_index("posted_at")
        .resample("MS")
        .size()
        .rename("opportunities")
        .reset_index()
    )
    roles = frame["role"].value_counts().head(8).sort_values().reset_index()
    roles.columns = ["role", "opportunities"]
    locations = frame["location"].value_counts().head(8).sort_values().reset_index()
    locations.columns = ["location", "opportunities"]
    work_modes = frame["work_mode"].value_counts().reset_index()
    work_modes.columns = ["work_mode", "opportunities"]

    core_demand = {
        skill: int(skill_counts.get(skill, 0))
        for skill in ("SQL", "Python", "Power BI")
    }

    return {
        "metrics": {
            "opportunities": rows,
            "roles": int(frame["role"].nunique()) if rows else 0,
            "locations": int(frame["location"].nunique()) if rows else 0,
            "core_skills": core_demand,
        },
        "charts": {
            "skills": _figure_json(
                px.bar(
                    top_skills,
                    x="opportunities",
                    y="skill",
                    orientation="h",
                    labels={"opportunities": "Listings mentioning skill", "skill": ""},
                    color="opportunities",
                    color_continuous_scale=["#51d8ef", "#4778ff"],
                ).update_layout(coloraxis_showscale=False, yaxis={"categoryorder": "total ascending"})
            ),
            "trend": _figure_json(
                px.line(
                    by_month,
                    x="posted_at",
                    y="opportunities",
                    markers=True,
                    labels={"posted_at": "", "opportunities": "Listings"},
                )
            ),
            "roles": _figure_json(
                px.bar(
                    roles,
                    x="opportunities",
                    y="role",
                    orientation="h",
                    labels={"opportunities": "Listings", "role": ""},
                    color_discrete_sequence=["#9274f6"],
                ).update_layout(yaxis={"categoryorder": "total ascending"})
            ),
            "locations": _figure_json(
                px.bar(
                    locations,
                    x="opportunities",
                    y="location",
                    orientation="h",
                    labels={"opportunities": "Listings", "location": ""},
                    color_discrete_sequence=["#2dbfc2"],
                ).update_layout(yaxis={"categoryorder": "total ascending"})
            ),
            "work_modes": _figure_json(
                px.pie(
                    work_modes,
                    names="work_mode",
                    values="opportunities",
                    hole=0.64,
                    color_discrete_sequence=["#527bff", "#2dbfc2", "#9274f6", "#9aa7b8"],
                )
            ),
        },
    }


def filter_options(frame: pd.DataFrame) -> dict[str, list[str]]:
    skills = sorted({skill for items in frame["skills"] for skill in _split_skills(items)})
    return {
        "locations": sorted(frame["location"].dropna().unique().tolist()),
        "roles": sorted(frame["role"].dropna().unique().tolist()),
        "skills": skills,
        "experience": sorted(frame["experience"].dropna().unique().tolist()),
        "min_date": frame["posted_at"].min().date().isoformat(),
        "max_date": frame["posted_at"].max().date().isoformat(),
    }


def source_details(frame: pd.DataFrame) -> list[dict[str, str]]:
    sources = frame[["source", "source_url"]].drop_duplicates()
    details: list[dict[str, str]] = []
    for row in sources.itertuples(index=False):
        label = str(row.source).strip() or "Source not specified"
        source_url = str(row.source_url).strip()
        parsed_url = urlparse(source_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            source_url = ""
        details.append({"label": label, "url": source_url})
    return details


def refresh_market_data(
    source: str,
    source_format: str,
    destination: Path,
    table_index: int = 0,
) -> int:
    source_format = source_format.lower()
    if source_format not in {"csv", "json", "html"}:
        raise ValueError("Source format must be csv, json or html.")
    if table_index < 0:
        raise ValueError("HTML table index must be zero or greater.")

    raw = _read_source(source, source_format)
    try:
        if source_format == "csv":
            source_frame = pd.read_csv(io.BytesIO(raw))
        elif source_format == "json":
            payload = json.loads(raw.decode("utf-8"))
            if isinstance(payload, dict):
                payload = payload.get("data", payload.get("results", payload))
            if not isinstance(payload, list):
                raise ValueError("JSON source must contain an array of market records.")
            source_frame = pd.DataFrame(payload)
        else:
            tables = pd.read_html(io.StringIO(raw.decode("utf-8-sig")))
            if table_index >= len(tables):
                raise ValueError(
                    f"HTML source has {len(tables)} table(s); table index {table_index} is unavailable."
                )
            source_frame = tables[table_index]
    except (UnicodeDecodeError, json.JSONDecodeError, pd.errors.ParserError) as error:
        raise ValueError(f"Could not parse {source_format.upper()} source: {error}") from error
    except ImportError as error:
        raise ValueError("Install lxml to read public HTML table sources.") from error
    except ValueError as error:
        if source_format == "html":
            raise ValueError(f"Could not parse HTML table source: {error}") from error
        raise

    normalized = _normalize_frame(source_frame)
    if normalized.empty:
        raise ValueError("The source contains no usable market records.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination = destination.resolve()
    manifest_path = destination.with_suffix(".json")
    source_label = _source_label(source)
    updated_at = datetime.now(timezone.utc).isoformat()
    manifest = {
        "source": source_label,
        "updated_at": updated_at,
        "methodology": (
            f"The information comes from {source_label}."
            f"{' We used table ' + str(table_index) + ' on that page.' if source_format == 'html' else ''} "
            "Job titles, places and dates are shown as the source provided them. "
            "A record is counted once for each skill it mentions. Filters only show "
            "records that match your choices. The source may not include every job."
        ),
        "demo": "false",
    }

    _atomic_write(normalized.to_csv(index=False).encode("utf-8"), destination)
    _atomic_write(json.dumps(manifest, indent=2).encode("utf-8"), manifest_path)
    return len(normalized)


def _read_source(source: str, source_format: str) -> bytes:
    parsed = urlparse(source)
    if parsed.scheme:
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("Remote sources must use HTTPS.")
        request = Request(
            source,
            headers={
                "Accept": "text/csv, application/json, text/html",
                "User-Agent": "VumbuaMarketData/1.0",
            },
        )
        try:
            with urlopen(request, timeout=15) as response:
                if urlparse(response.geturl()).scheme != "https":
                    raise ValueError("Market data source redirects away from HTTPS.")
                content_type = response.headers.get_content_type()
                accepted_types = {
                    "text/csv",
                    "application/csv",
                    "application/json",
                    "text/plain",
                    "application/octet-stream",
                }
                if source_format == "html":
                    accepted_types.update({"text/html", "application/xhtml+xml"})
                if content_type not in accepted_types:
                    raise ValueError(f"Unsupported source content type: {content_type}.")
                raw = response.read(MAX_SOURCE_BYTES + 1)
        except URLError as error:
            raise ValueError(f"Could not retrieve market data source: {error}") from error
    else:
        try:
            with open(source, "rb") as source_file:
                raw = source_file.read(MAX_SOURCE_BYTES + 1)
        except OSError as error:
            raise ValueError(f"Could not read market data source: {error}") from error

    if len(raw) > MAX_SOURCE_BYTES:
        raise ValueError("Market data source exceeds the 25 MB size limit.")
    if not raw:
        raise ValueError("Market data source is empty.")
    return raw


def _normalize_frame(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.rename(columns={column: str(column).strip().lower() for column in frame.columns})
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Market data is missing required columns: {', '.join(missing)}.")

    for column, default in OPTIONAL_DEFAULTS.items():
        if column not in frame.columns:
            frame[column] = default

    normalized = frame[
        [*REQUIRED_COLUMNS, *OPTIONAL_DEFAULTS.keys()]
    ].copy()
    normalized["posted_at"] = pd.to_datetime(
        normalized["posted_at"], errors="coerce", utc=True
    ).dt.tz_convert(None)
    if normalized["posted_at"].isna().any():
        invalid_count = int(normalized["posted_at"].isna().sum())
        raise ValueError(f"{invalid_count} market record(s) have an invalid posted_at date.")

    for column in ("role", "location", "experience", "work_mode", "source", "source_url"):
        normalized[column] = (
            normalized[column].astype("string").fillna("").astype(str).str.strip()
        )
    normalized["skills"] = normalized["skills"].apply(_skills_to_string)
    for column in ("role", "location", "skills"):
        if normalized[column].eq("").any():
            raise ValueError(f"Market records must have a non-empty {column} value.")
    for column, default in OPTIONAL_DEFAULTS.items():
        normalized[column] = normalized[column].replace("", default)

    return normalized.sort_values("posted_at").reset_index(drop=True)


def _skills_to_string(value) -> str:
    if isinstance(value, list):
        return " | ".join(str(item).strip() for item in value if str(item).strip())
    if pd.isna(value):
        return ""
    return str(value).strip()


def _split_skills(value: str) -> list[str]:
    return [skill.strip() for skill in str(value).split("|") if skill.strip()]


def _skill_counts(frame: pd.DataFrame) -> pd.Series:
    counts: dict[str, int] = {}
    for skills in frame["skills"]:
        for skill in _split_skills(skills):
            counts[skill] = counts.get(skill, 0) + 1
    return pd.Series(counts, dtype="int64").sort_values(ascending=False)


def _literal_pattern(value: str) -> str:
    import re

    return re.escape(value)


def _figure_json(figure: go.Figure) -> dict:
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Manrope, sans-serif", "color": "#c5cfdf", "size": 11},
        margin={"l": 8, "r": 14, "t": 12, "b": 12},
        xaxis={"gridcolor": "rgba(255,255,255,0.08)", "zerolinecolor": "rgba(255,255,255,0.08)"},
        yaxis={"gridcolor": "rgba(255,255,255,0.08)", "zerolinecolor": "rgba(255,255,255,0.08)"},
        showlegend=False,
        autosize=True,
    )
    return json.loads(figure.to_json())


def _source_label(source: str) -> str:
    parsed = urlparse(source)
    return parsed.netloc if parsed.netloc else Path(source).name


def _atomic_write(contents: bytes, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_path = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    try:
        with os.fdopen(file_descriptor, "wb") as target:
            target.write(contents)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary_path, destination)
    except Exception:
        try:
            os.unlink(temporary_path)
        except FileNotFoundError:
            pass
        raise
