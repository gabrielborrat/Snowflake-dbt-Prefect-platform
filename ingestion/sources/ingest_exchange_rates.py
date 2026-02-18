"""
Exchange Rates Ingestion Script
--------------------------------
Loads daily FX rates from frankfurter.app (ECB data) into Snowflake RAW.EXCHANGE_RATES.

Source: https://api.frankfurter.app (ECB reference rates)
Target: RAW.EXCHANGE_RATES.DAILY_RATES

Features:
- Incremental by date range (fetches only new data)
- Idempotent: MERGE on (base_currency, target_currency, date)
- EUR base currency with configurable targets
- Structured logging
- Audit column (_loaded_at)

Usage:
    python -m ingestion.sources.ingest_exchange_rates
"""

from datetime import datetime, timedelta
import requests
import pandas as pd
from ingestion.config import (
    SNOWFLAKE_DATABASE,
    RAW_EXCHANGE_RATES_SCHEMA,
    FX_BASE_CURRENCY,
    FX_TARGET_CURRENCIES,
    FX_API_BASE_URL,
)
from ingestion.utils.snowflake_connector import (
    get_snowflake_connection,
    execute_query,
    merge_dataframe,
)
from ingestion.utils.logging_config import setup_logger

log = setup_logger("ingest_exchange_rates")

# --- Configuration ---
TABLE_NAME = "DAILY_RATES"
DEFAULT_START_DATE = "2020-01-01"
MAX_DAYS_PER_REQUEST = 365  # API handles large ranges, but we chunk for safety

# DDL for the target table
CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {SNOWFLAKE_DATABASE}.{RAW_EXCHANGE_RATES_SCHEMA}.{TABLE_NAME} (
    base_currency           VARCHAR,
    target_currency         VARCHAR,
    date                    DATE,
    rate                    FLOAT,
    _loaded_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
"""

# Columns to load (excludes _loaded_at)
LOAD_COLUMNS = [
    "base_currency",
    "target_currency",
    "date",
    "rate",
]


def get_last_loaded_date(conn) -> str:
    """
    Get the most recent date loaded for exchange rates.
    Returns DEFAULT_START_DATE if no data exists.
    """
    query = f"""
        SELECT MAX(date) AS last_date
        FROM {SNOWFLAKE_DATABASE}.{RAW_EXCHANGE_RATES_SCHEMA}.{TABLE_NAME}
    """
    try:
        result = execute_query(conn, query)
        if result and result[0][0]:
            last_date = result[0][0]
            next_date = (
                pd.to_datetime(last_date) + timedelta(days=1)
            ).strftime("%Y-%m-%d")
            log.info(f"Last loaded date: {last_date} → fetching from {next_date}")
            return next_date
    except Exception:
        pass

    log.info(f"No existing data → fetching from {DEFAULT_START_DATE}")
    return DEFAULT_START_DATE


def fetch_exchange_rates(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch daily exchange rates from frankfurter.app API.

    Args:
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).

    Returns:
        DataFrame with daily exchange rate data.
    """
    targets = ",".join(FX_TARGET_CURRENCIES)
    url = f"{FX_API_BASE_URL}/{start_date}..{end_date}"
    params = {
        "from": FX_BASE_CURRENCY,
        "to": targets,
    }

    log.info(f"Fetching FX rates: {FX_BASE_CURRENCY} → {targets} ({start_date} to {end_date})")

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Parse the response into rows
        rows = []
        rates_data = data.get("rates", {})

        for date_str, rates in rates_data.items():
            for target_currency, rate in rates.items():
                rows.append(
                    {
                        "base_currency": FX_BASE_CURRENCY,
                        "target_currency": target_currency,
                        "date": date_str,
                        "rate": rate,
                    }
                )

        if not rows:
            log.warning("No rate data returned from API")
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"]).dt.date

        # Order columns
        df = df[LOAD_COLUMNS]

        log.info(f"Fetched {len(df)} rate records ({len(rates_data)} days × {len(FX_TARGET_CURRENCIES)} currencies)")
        return df

    except requests.exceptions.RequestException as e:
        log.error(f"API request failed: {e}")
        return pd.DataFrame()
    except Exception as e:
        log.error(f"Failed to parse FX data: {e}")
        return pd.DataFrame()


def ingest_exchange_rates():
    """Main ingestion function for exchange rate data."""
    log.info("=" * 60)
    log.info("Starting exchange rates ingestion")
    log.info(f"Base: {FX_BASE_CURRENCY} → Targets: {FX_TARGET_CURRENCIES}")
    log.info("=" * 60)

    end_date = datetime.now().strftime("%Y-%m-%d")

    with get_snowflake_connection(
        schema=RAW_EXCHANGE_RATES_SCHEMA
    ) as conn:
        # Ensure target table exists
        execute_query(conn, CREATE_TABLE_SQL)
        log.info(f"Table {TABLE_NAME} ready.")

        # Get incremental start date
        start_date = get_last_loaded_date(conn)

        # Check if we need to fetch
        if start_date >= end_date:
            log.info("Data is already up to date — nothing to fetch.")
            return

        # Fetch data in chunks (for very large date ranges)
        total_rows = 0
        chunk_start = pd.to_datetime(start_date)
        chunk_end_limit = pd.to_datetime(end_date)

        while chunk_start < chunk_end_limit:
            chunk_end = min(
                chunk_start + timedelta(days=MAX_DAYS_PER_REQUEST),
                chunk_end_limit,
            )

            df = fetch_exchange_rates(
                chunk_start.strftime("%Y-%m-%d"),
                chunk_end.strftime("%Y-%m-%d"),
            )

            if not df.empty:
                rows = merge_dataframe(
                    conn=conn,
                    df=df,
                    table_name=TABLE_NAME,
                    schema=RAW_EXCHANGE_RATES_SCHEMA,
                    database=SNOWFLAKE_DATABASE,
                    merge_keys=["base_currency", "target_currency", "date"],
                )
                total_rows += rows

            chunk_start = chunk_end + timedelta(days=1)

        log.info("=" * 60)
        log.info(f"✅ Exchange rates ingestion complete — {total_rows} total rows loaded")
        log.info("=" * 60)


if __name__ == "__main__":
    ingest_exchange_rates()
