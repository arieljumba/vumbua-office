import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

from config import load_settings
from routes import ROUTES


BASE_DIR = Path(__file__).resolve().parent
SQL_DIR = BASE_DIR / "sql"


def validate_routes_against_sql(routes: dict[str, str]) -> None:
    sql_queries = {p.stem for p in SQL_DIR.glob("*.sql")}
    route_queries = set(routes.keys())

    missing_sql = sorted(route_queries - sql_queries)

    # The pipeline should run only what is configured in routes.py.
    if missing_sql:
        raise ValueError(
            "Route entries without SQL files: " + ", ".join(missing_sql)
        )


def run_etl(
    query_name: str,
    local_table: str,
    local_schema: str,
    remote_engine,
    local_engine,
) -> None:
    sql_file = SQL_DIR / f"{query_name}.sql"
    if not sql_file.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_file}")

    # Trino via SQLAlchemy expects a single statement without a trailing semicolon.
    query = sql_file.read_text(encoding="utf-8").strip().rstrip(";")
    df = pd.read_sql_query(query, remote_engine)

    with local_engine.begin() as conn:
        conn.exec_driver_sql(f'CREATE SCHEMA IF NOT EXISTS "{local_schema}"')

    # Replace table if it exists; create it automatically if it does not.
    df.to_sql(
        local_table,
        local_engine,
        schema=local_schema,
        if_exists="replace",
        index=False,
    )
    print(f"Loaded {len(df)} rows: {query_name} -> {local_schema}.{local_table}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run ETL from remote DB to local Postgres"
    )
    parser.add_argument(
        "--query",
        help="Run only one query route by query name (example: fetch_activity)",
    )
    args = parser.parse_args()

    settings = load_settings()
    routes = ROUTES
    if not routes:
        raise ValueError("No route mappings found. Add mappings to routes.py")

    remote_engine = create_engine(
        settings.remote_db_url,
        connect_args=settings.remote_connect_args,
    )
    local_engine = create_engine(settings.local_db_url)

    if args.query:
        if args.query not in routes:
            raise ValueError(f"Query route not found: {args.query}")
        run_etl(
            args.query,
            routes[args.query],
            settings.local_schema,
            remote_engine,
            local_engine,
        )
        return

    # Full run mode enforces 1:1 consistency between configured routes and SQL files.
    validate_routes_against_sql(routes)

    for query_name, local_table in routes.items():
        run_etl(
            query_name,
            local_table,
            settings.local_schema,
            remote_engine,
            local_engine,
        )


if __name__ == "__main__":
    main()
