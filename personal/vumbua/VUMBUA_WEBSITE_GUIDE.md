# Vumbua Website Guide

This guide explains what the Vumbua website is for, what visitors can do on it, and how its main parts work. It is written for the Vumbua team as well as anyone maintaining the site.

## What Vumbua offers

Vumbua's flagship course is the **3-in-1 Data Analytics Program**. It teaches SQL, Python and Power BI as connected steps in one four-month learning journey:

1. **SQL gets the data.** Learners find information in databases and answer questions with queries.
2. **Python works with the data.** Learners clean, organise and analyse information, and can automate repeat tasks.
3. **Power BI communicates the insight.** Learners build reports and dashboards that help other people understand what the analysis found.
4. **A practical project brings it together.** Learners start with a business question and take it from raw data to a clear finding.

The program is for beginners, people changing careers, people who work with spreadsheets or reports, people building on existing analytics skills, and organizations looking for team training. Learners do not need previous SQL, Python or Power BI experience. Industry-experienced analytics professionals teach how the tools are used in working environments.

Classes are live and cohort-based, meeting three times a week. Scheduling is flexible to accommodate learners' routines, and assignments provide practice between sessions. The next cohort starts in December.

The program costs **KES 20,000 per month for four months (KES 80,000 total)**. Learners who successfully complete it receive the **Vumbua Certificate of Completion: 3-in-1 Data Analytics Program**. The certificate is not presented as an external accreditation.

## Pages visitors can use

### Home

The home page introduces Vumbua and explains who the program is for. It shows how SQL, Python and Power BI fit together, outlines the four-month progression, gives examples of practical business questions, and links to the program, Market Insights and enquiry form.

### Program

The Program page gives the month-by-month outline:

- Month 1: SQL, databases, queries, joins, analysis and data quality.
- Month 2: Python, Pandas, cleaning, analysis and automation.
- Month 3: Power BI, data models, DAX, dashboards and communicating results.
- Month 4: a project using the complete `Raw data → SQL → Python → Power BI → Business insight` workflow.

It also explains the certificate and displays the full program investment near the end of the page.

### Market Insights

Market Insights is a **practice dashboard**, not a job board. It demonstrates how someone can filter records and compare skills, roles, locations, dates and work arrangements.

At present, the built-in records are synthetic examples prepared for demonstrating the dashboard. They are **not actual vacancies**, do not describe the current job market, and should not be used to make career or hiring decisions.

To explore the dashboard:

1. Choose a location, role, skill, experience level or date range.
2. Select **Show results**.
3. Compare the updated numbers and charts. Choose **Clear** to start again.

The records shown, source names or links, last-updated time and a plain-language description of how the results were prepared are displayed on the page. A skill count means the number of records that mention that skill; a single record can mention more than one skill.

When a permitted real dataset is configured, the site shows its source and the source details available in that dataset. The presence of a source link does not mean that Vumbua has independently verified that source's coverage or accuracy.

### Contact

The enquiry form lets a person ask about the individual program or corporate team training. It asks for contact details, current occupation, experience level, preferred learning format and what they would like to learn or solve. The form checks required fields, saves valid enquiries in the site's SQLite database, and emails the enquiry to `info@vumbua.co.ke` through the configured SMTP service. If email delivery fails, the saved enquiry is retained and the visitor is told to contact Vumbua directly.

## How Market Insights data works

The dashboard uses:

- **Pandas** to load, check and filter the records.
- **Plotly** to draw interactive charts.
- A Flask endpoint at `/api/market-insights` to return the numbers and charts for the selected filters.
- A CSV file plus a small metadata JSON file to hold refreshed records, their source description, update time and methodology.

By default, the site uses `app/data/demo_market_roles.csv`. The page identifies this as synthetic demonstration data. No live job feed is configured in the project by default.

### Refresh from a permitted source

The command is:

```bash
flask --app wsgi:app refresh-market-data --source SOURCE --format FORMAT
```

Supported input formats:

- `csv` for a CSV file or HTTPS URL.
- `json` for a JSON array, or an object containing a `data` or `results` array.
- `html` for a page with a table that is permitted to reuse. Pick the table with `--table-index 0` (or another zero-based table number).

For example:

```bash
flask --app wsgi:app refresh-market-data --source ./roles.csv --format csv
flask --app wsgi:app refresh-market-data --source https://example.org/roles.json --format json
flask --app wsgi:app refresh-market-data --source https://example.org/roles --format html --table-index 0
```

Only use public data that its publisher permits you to reuse. Remote sources must use HTTPS. The refresh checks the required fields and dates before replacing the active file. It does not crawl arbitrary websites or bypass access controls.

The required data columns are:

| Column | What it means |
|---|---|
| `posted_at` | When the opportunity was posted |
| `role` | The job or opportunity title |
| `location` | The place listed by the source |
| `skills` | Skills mentioned, separated by `|` in CSV or as a list in JSON |

Optional columns are `experience`, `work_mode`, `source` and `source_url`. When supplied, `source_url` must be a normal HTTP or HTTPS address to be shown as a clickable source link. A source must never be invented to fill a gap.

## What happens to an enquiry

1. A visitor opens `/contact` and completes the form.
2. A CSRF token helps ensure the form submission came from the Vumbua website.
3. Flask checks the submitted values on the server. Invalid submissions are shown with an explanation and are not saved.
4. Valid submissions are stored in the `enquiries` table in SQLite. Database code is kept separate so the storage layer can be changed when a PostgreSQL migration is planned.

Enquiries contain personal contact details. Keep the database private, restrict server access, protect backups, and decide how long records should be kept. The application does not currently include an enquiry-management dashboard or send notification emails.

## How the website is organized

The site uses Flask, Jinja templates, CSS, JavaScript, Pandas, Plotly and SQLite.

```text
vumbua/
├── app/
│   ├── __init__.py              App setup, security headers and CLI commands
│   ├── config.py                Environment-based settings
│   ├── database.py              SQLite setup and enquiry storage
│   ├── models.py                Enquiry fields and validation
│   ├── routes/                  Home, program, dashboard and enquiry routes
│   ├── market_data/             Import, validation, filtering and charts
│   ├── templates/               Jinja page layouts and page content
│   ├── static/css/site.css      Shared responsive visual design
│   ├── static/js/               Navigation and dashboard interactions
│   └── data/                    Bundled synthetic practice records
├── deploy/                      Nginx and systemd examples
├── tests/                       Automated route, form and dashboard tests
├── .env.example                 Configuration template; contains no secrets
├── requirements.txt             Python package requirements
├── wsgi.py                      Gunicorn entry point
└── README.md                    Setup and deployment instructions
```

## Run and check the site

From the `vumbua` folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
flask --app wsgi:app run --debug
```

Then open <http://127.0.0.1:5000>. To run the automated checks:

```bash
pytest
```

For production, set a unique `SECRET_KEY` of at least 32 characters in `.env`, use persistent storage for the database and refreshed data, and follow the Ubuntu, Gunicorn, Nginx and HTTPS instructions in [README.md](./README.md). Never commit `.env` or enquiry records.

## Important limits

- The bundled Market Insights records are synthetic examples, not current job-market data.
- A configured source can be incomplete, delayed or inaccurate. Check its terms, coverage and update frequency before relying on it.
- The program certificate is a Vumbua completion certificate; the site makes no unsupported accreditation claim.
- Corporate training is available by enquiry; the site does not promise a fixed corporate package or price.
