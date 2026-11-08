import json


def test_market_insights_page_discloses_demo_source_and_methodology(client):
    response = client.get("/market-insights")

    assert response.status_code == 200
    assert b"PRACTICE DATA" in response.data
    assert b"synthetic" in response.data
    assert b"SOURCE FILE OR FEED" in response.data
    assert b"LAST UPDATED" in response.data
    assert b"HOW TO READ THIS" in response.data
    assert b"What is this dashboard?" in response.data
    assert b"Show results" in response.data
    assert b"Where the data comes from" in response.data
    assert "DEMO — synthetic records".encode() in response.data


def test_dashboard_api_returns_filtered_pandas_and_plotly_data(client):
    response = client.get("/api/market-insights?location=Nairobi&skill=SQL")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["metrics"]["opportunities"] > 0
    assert payload["metrics"]["opportunities"] < 38
    assert payload["metadata"]["demo"] == "true"
    assert {"skills", "trend", "roles", "locations", "work_modes"} <= set(
        payload["charts"]
    )
    assert payload["charts"]["skills"]["data"]
    assert payload["filters"]["location"] == "Nairobi"
    assert payload["sources"] == [
        {"label": "DEMO — synthetic records", "url": ""}
    ]


def test_dashboard_rejects_invalid_date_filter(client):
    response = client.get("/api/market-insights?start_date=not-a-date")

    assert response.status_code == 400
    assert "YYYY-MM-DD" in response.get_json()["error"]


def test_dashboard_rejects_unknown_role(client):
    response = client.get("/api/market-insights?role=untrusted-role")

    assert response.status_code == 400
    assert "available filters" in response.get_json()["error"]


def test_refresh_command_validates_and_replaces_data(client, app, tmp_path):
    source = tmp_path / "public-export.json"
    source.write_text(
        json.dumps(
            [
                {
                    "posted_at": "2026-10-01",
                    "role": "Data Analyst",
                    "location": "Nairobi",
                    "skills": ["SQL", "Python"],
                    "experience": "Entry level",
                    "work_mode": "Remote",
                }
            ]
        ),
        encoding="utf-8",
    )

    result = app.test_cli_runner().invoke(
        args=[
            "refresh-market-data",
            "--source",
            str(source),
            "--format",
            "json",
        ]
    )

    assert result.exit_code == 0, result.output
    assert "1 validated records" in result.output
    payload = client.get("/api/market-insights").get_json()
    assert payload["metrics"]["opportunities"] == 1
    assert payload["metadata"]["demo"] == "false"
    assert payload["metadata"]["source"] == "public-export.json"
    assert "information comes from public-export.json" in payload["metadata"]["methodology"]


def test_refresh_command_accepts_a_permitted_html_table(client, app, tmp_path):
    source = tmp_path / "public-page.html"
    source.write_text(
        "<table><thead><tr><th>posted_at</th><th>role</th><th>location</th>"
        "<th>skills</th></tr></thead><tbody><tr><td>2026-10-01</td>"
        "<td>Data Analyst</td><td>Nairobi</td><td>SQL | Python</td></tr></tbody></table>",
        encoding="utf-8",
    )

    result = app.test_cli_runner().invoke(
        args=[
            "refresh-market-data",
            "--source",
            str(source),
            "--format",
            "html",
            "--table-index",
            "0",
        ]
    )

    assert result.exit_code == 0, result.output
    assert "1 validated records" in result.output
    payload = client.get("/api/market-insights").get_json()
    assert payload["metrics"]["opportunities"] == 1
    assert "We used table 0" in payload["metadata"]["methodology"]


def test_refreshed_sources_are_available_as_safe_dashboard_links(client, app, tmp_path):
    source = tmp_path / "roles.csv"
    source.write_text(
        "posted_at,role,location,skills,source,source_url\n"
        "2026-10-01,Data Analyst,Nairobi,SQL,Public dataset,"
        "https://example.org/jobs/1\n"
        "2026-10-02,Reporting Analyst,Mombasa,Power BI,Unsafe link,"
        "javascript:alert(1)\n",
        encoding="utf-8",
    )

    result = app.test_cli_runner().invoke(
        args=[
            "refresh-market-data",
            "--source",
            str(source),
            "--format",
            "csv",
        ]
    )

    assert result.exit_code == 0, result.output
    response = client.get("/api/market-insights")
    sources = response.get_json()["sources"]
    assert sources[0] == {
        "label": "Public dataset",
        "url": "https://example.org/jobs/1",
    }
    assert sources[1] == {"label": "Unsafe link", "url": ""}


def test_refresh_rejects_non_https_remote_source(app):
    result = app.test_cli_runner().invoke(
        args=[
            "refresh-market-data",
            "--source",
            "http://example.org/roles.csv",
            "--format",
            "csv",
        ]
    )

    assert result.exit_code != 0
    assert "must use HTTPS" in result.output
