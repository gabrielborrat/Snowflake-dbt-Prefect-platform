"""
Market Prices Ingestion Script
-------------------------------
Loads daily stock prices from Yahoo Finance API into Snowflake RAW.MARKET_DATA.

Source: yfinance Python library (Yahoo Finance)
Target: RAW.MARKET_DATA.DAILY_PRICES

Features:
- Incremental by date range (fetches only new data)
- Idempotent: MERGE on (ticker, date)
- Multi-ticker support (configurable in config.py)
- Structured logging
- Audit column (_loaded_at)

Usage:
    python -m ingestion.sources.ingest_market_prices
"""

from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
from ingestion.config import (
    SNOWFLAKE_DATABASE,
    RAW_MARKET_DATA_SCHEMA,
    MARKET_TICKERS,
)
from ingestion.utils.snowflake_connector import (
    get_snowflake_connection,
    execute_query,
    merge_dataframe,
)
from ingestion.utils.logging_config import setup_logger

log = setup_logger("ingest_market_prices")

# --- Configuration ---
TABLE_NAME = "DAILY_PRICES"
DEFAULT_START_DATE = "2020-01-01"

# DDL for the target table
CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {SNOWFLAKE_DATABASE}.{RAW_MARKET_DATA_SCHEMA}.{TABLE_NAME} (
    ticker                  VARCHAR,
    date                    DATE,
    open                    FLOAT,
    high                    FLOAT,
    low                     FLOAT,
    close                   FLOAT,
    adj_close               FLOAT,
    volume                  NUMBER,
    _loaded_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
"""

# Columns to load (excludes _loaded_at)
LOAD_COLUMNS = [
    "ticker",
    "date",
    "open",
    "high",
    "low",
    "close",
    "adj_close",
    "volume",
]


def get_last_loaded_date(conn, ticker: str) -> str:
    """
    Get the most recent date loaded for a given ticker.
    Returns DEFAULT_START_DATE if no data exists.
    """
    query = f"""
        SELECT MAX(date) AS last_date
        FROM {SNOWFLAKE_DATABASE}.{RAW_MARKET_DATA_SCHEMA}.{TABLE_NAME}
        WHERE ticker = %s
    """
    try:
        result = execute_query(conn, query, (ticker,))
        if result and result[0][0]:
            # Start from the day after the last loaded date
            last_date = result[0][0]
            next_date = (
                pd.to_datetime(last_date) + timedelta(days=1)
            ).strftime("%Y-%m-%d")
            log.info(f"Last loaded date for {ticker}: {last_date} → fetching from {next_date}")
            return next_date
    except Exception:
        pass

    log.info(f"No existing data for {ticker} → fetching from {DEFAULT_START_DATE}")
    return DEFAULT_START_DATE


def fetch_ticker_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch daily OHLCV data for a single ticker from Yahoo Finance.

    Args:
        ticker: Stock ticker symbol.
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).

    Returns:
        DataFrame with daily price data.
    """
    log.info(f"Fetching {ticker} from {start_date} to {end_date}")

    try:
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date, auto_adjust=False)

        if df.empty:
            log.warning(f"No data returned for {ticker}")
            return pd.DataFrame()

        # Reset index (date becomes a column)
        df = df.reset_index()

        # Standardize column names
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        # Add ticker column
        df["ticker"] = ticker

        # Rename columns to match our schema
        column_mapping = {
            "adj_close": "adj_close",
            "adj close": "adj_close",
        }
        df = df.rename(columns=column_mapping)

        # Convert date to date type (remove timezone if present)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date

        # Select and order columns
        available_columns = [c for c in LOAD_COLUMNS if c in df.columns]
        df = df[available_columns]

        # Replace NaN with None
        df = df.where(pd.notna(df), None)

        log.info(f"Fetched {len(df)} rows for {ticker}")
        return df

    except Exception as e:
        log.error(f"Failed to fetch {ticker}: {e}")
        return pd.DataFrame()


def ingest_market_prices():
    """Main ingestion function for market price data."""
    log.info("=" * 60)
    log.info("Starting market prices ingestion")
    log.info(f"Tickers: {MARKET_TICKERS}")
    log.info("=" * 60)

    end_date = datetime.now().strftime("%Y-%m-%d")

    with get_snowflake_connection(
        schema=RAW_MARKET_DATA_SCHEMA
    ) as conn:
        # Ensure target table exists
        execute_query(conn, CREATE_TABLE_SQL)
        log.info(f"Table {TABLE_NAME} ready.")

        total_rows = 0
        success_count = 0
        fail_count = 0

        for ticker in MARKET_TICKERS:
            try:
                # Get incremental start date
                start_date = get_last_loaded_date(conn, ticker)

                # Fetch data from Yahoo Finance
                df = fetch_ticker_data(ticker, start_date, end_date)

                if not df.empty:
                    # MERGE into target (idempotent upsert)
                    rows = merge_dataframe(
                        conn=conn,
                        df=df,
                        table_name=TABLE_NAME,
                        schema=RAW_MARKET_DATA_SCHEMA,
                        database=SNOWFLAKE_DATABASE,
                        merge_keys=["ticker", "date"],
                    )
                    total_rows += rows
                    success_count += 1
                else:
                    log.info(f"No new data for {ticker} — skipping.")
                    success_count += 1

            except Exception as e:
                log.error(f"Failed to process {ticker}: {e}")
                fail_count += 1

        log.info("=" * 60)
        log.info(
            f"✅ Market prices ingestion complete — "
            f"{total_rows} rows loaded, "
            f"{success_count} tickers succeeded, "
            f"{fail_count} tickers failed"
        )
        log.info("=" * 60)


if __name__ == "__main__":
    ingest_market_prices()
