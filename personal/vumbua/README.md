# Vumbua

A Flask website for the Vumbua 3-in-1 Data Analytics Program, with an interactive market-insights demonstration and a SQLite enquiry form.

For a plain-language explanation of the pages, course, data dashboard, enquiry flow and project structure, see [VUMBUA_WEBSITE_GUIDE.md](./VUMBUA_WEBSITE_GUIDE.md).

## Run locally

Python 3.11 or newer is recommended.

```bash
cd /path/to/vumbua
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
flask --app wsgi:app run --debug
```

Open <http://127.0.0.1:5000>. The app creates its SQLite database on startup. The website works without a configured live market feed; in that case, the dashboard uses the bundled, synthetic demonstration dataset and identifies it as such.

Run the test suite:

```bash
pytest
```

## Market data

The dashboard uses Pandas for validated records and filtered analysis and Plotly for its charts. The bundled CSV is intentionally synthetic: it is not a sample of current vacancies and must not be presented as actual hiring demand.

To refresh from a permitted public CSV/JSON endpoint, a permitted website table, or a local export, set `MARKET_DATA_SOURCE_URL` and `MARKET_DATA_SOURCE_FORMAT` in `.env`, then run:

```bash
flask --app wsgi:app refresh-market-data
```

Or pass a source directly:

```bash
flask --app wsgi:app refresh-market-data --source ./market-export.csv --format csv
flask --app wsgi:app refresh-market-data --source https://example.org/public/roles.json --format json
flask --app wsgi:app refresh-market-data --source https://example.org/public/roles --format html --table-index 0
```

Only use sources whose terms permit reuse. Remote sources must use HTTPS; redirects away from HTTPS are rejected. API responses may be a JSON array or an object containing a `data` or `results` array. An HTML source must be a permitted page containing a table with the canonical column names below; choose its zero-based index with `--table-index` or `MARKET_DATA_TABLE_INDEX`. The CLI does not crawl arbitrary pages. The canonical columns are:

| Column | Required | Meaning |
|---|---:|---|
| `posted_at` | Yes | A date or timestamp for the record |
| `role` | Yes | Role title |
| `location` | Yes | Location label |
| `skills` | Yes | Pipe-separated string or JSON array of skill names |
| `experience` | No | Experience requirement; defaults to `Not specified` |
| `work_mode` | No | Remote, hybrid, onsite, or source-specific value |
| `source` | No | Attribution carried with each record |
| `source_url` | No | Source record URL |

Refresh validates the schema and dates before writing the new CSV and a companion metadata file into `instance/`. The dashboard displays that attribution, the refresh timestamp and its methodology. New adapters should honor the publisher's access rules, terms and robots policy, then normalize the result to this schema.

Filters are applied server-side for location, role, skill, experience and date range. The API endpoint is `GET /api/market-insights`.

## Enquiries and database

The enquiry form is protected by Flask-WTF CSRF tokens, validates fields server-side, and saves submissions to SQLite. Database access and the schema live behind `app/database.py`; form values are represented by `app/models.py`. This boundary keeps the application logic separate from the current SQLite driver when a PostgreSQL repository/driver is introduced.

For production, set `DATABASE_PATH` to a persistent absolute path. SQLite is suitable for the initial single-host deployment; use PostgreSQL for multi-instance scaling or higher write concurrency. Enquiry data should be handled with appropriate retention, access controls and backups.

## Configuration

Copy `.env.example` to `.env`. Important settings:

| Variable | Purpose |
|---|---|
| `FLASK_ENV` | `development` locally; use `production` on the server |
| `SECRET_KEY` | Long, unique random value required in production |
| `DATABASE_PATH` | SQLite database location |
| `MARKET_DATA_FILE` | Active market CSV location |
| `MARKET_DATA_SOURCE_URL` | Optional permitted public CSV/JSON/HTML source or local file |
| `MARKET_DATA_SOURCE_FORMAT` | `csv`, `json` or `html` |
| `MARKET_DATA_TABLE_INDEX` | Selected public HTML table index |
| `LOG_LEVEL` / `LOG_FILE` | Application log level and optional rotating log file |

Do not commit `.env`, database files or live enquiry records.

## Ubuntu deployment: Gunicorn, Nginx and HTTPS

The deployment uses a dedicated unprivileged `vumbua` account, Gunicorn on loopback and Nginx for TLS termination. Point `vumbua.co.ke` and `www.vumbua.co.ke` to the server first.

1. Install Python, Nginx and Certbot; create `/srv/vumbua`, a virtual environment and a `vumbua` service account. Copy this project to `/srv/vumbua`, install `requirements.txt`, and create `/srv/vumbua/.env` with `FLASK_ENV=production`, a unique secret, and persistent absolute database/data paths. Restrict `.env` and `instance/` to the service account.
2. Initialize the database and verify the WSGI app:

   ```bash
   cd /srv/vumbua
   sudo -u vumbua .venv/bin/flask --app wsgi:app init-db
   sudo -u vumbua .venv/bin/gunicorn --config gunicorn.conf.py wsgi:app
   ```

3. Install the systemd unit:

   ```bash
   sudo cp deploy/vumbua.service /etc/systemd/system/vumbua.service
   sudo systemctl daemon-reload
   ```

4. Obtain the TLS certificate with Certbot, install `deploy/nginx-vumbua.conf` as `/etc/nginx/sites-available/vumbua`, enable it, then test and reload Nginx:

   ```bash
   sudo certbot certonly --nginx -d vumbua.co.ke -d www.vumbua.co.ke
   sudo ln -s /etc/nginx/sites-available/vumbua /etc/nginx/sites-enabled/vumbua
   sudo nginx -t
   sudo systemctl reload nginx
   sudo systemctl enable --now vumbua
   ```

5. Confirm HTTP redirects to HTTPS, HTTPS serves the site, and renewal works with `sudo certbot renew --dry-run`.

Keep the app and OS patched, keep the SQLite/data directory persistent and backed up, and review access to enquiry records. TLS certificate paths in the Nginx sample assume the Certbot domain above.
