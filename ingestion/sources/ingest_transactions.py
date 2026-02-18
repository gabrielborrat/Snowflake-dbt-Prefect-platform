"""
Transaction Ingestion Script
-----------------------------
Loads credit card transaction data from Kaggle CSV into Snowflake RAW.TRANSACTIONS.

Source: https://www.kaggle.com/datasets/kartik2112/fraud-detection
Target: RAW.TRANSACTIONS.CREDIT_CARD_TRANSACTIONS

Features:
- Full load from CSV files
- Idempotent: truncate + load pattern (safe to re-run)
- Batch upload for memory efficiency
- Structured logging
- Audit column (_loaded_at)

Usage:
    python -m ingestion.sources.ingest_transactions
"""

import os
import glob
import pandas as pd
from ingestion.config import (
    SNOWFLAKE_DATABASE,
    RAW_TRANSACTIONS_SCHEMA,
)
from ingestion.utils.snowflake_connector import (
    get_snowflake_connection,
    execute_query,
    write_dataframe,
)
from ingestion.utils.logging_config import setup_logger

log = setup_logger("ingest_transactions")

# --- Configuration ---
TABLE_NAME = "CREDIT_CARD_TRANSACTIONS"
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data"
)

# DDL for the target table
CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {SNOWFLAKE_DATABASE}.{RAW_TRANSACTIONS_SCHEMA}.{TABLE_NAME} (
    trans_date_trans_time    TIMESTAMP,
    cc_num                  NUMBER(20,0),
    merchant                VARCHAR,
    category                VARCHAR,
    amt                     FLOAT,
    first                   VARCHAR,
    last                    VARCHAR,
    gender                  VARCHAR,
    street                  VARCHAR,
    city                    VARCHAR,
    state                   VARCHAR,
    zip                     VARCHAR,
    lat                     FLOAT,
    long                    FLOAT,
    city_pop                INTEGER,
    job                     VARCHAR,
    dob                     DATE,
    trans_num               VARCHAR,
    unix_time               NUMBER,
    merch_lat               FLOAT,
    merch_long              FLOAT,
    is_fraud                INTEGER,
    _loaded_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
"""

# Columns to load (excludes _loaded_at which has a default)
LOAD_COLUMNS = [
    "trans_date_trans_time",
    "cc_num",
    "merchant",
    "category",
    "amt",
    "first",
    "last",
    "gender",
    "street",
    "city",
    "state",
    "zip",
    "lat",
    "long",
    "city_pop",
    "job",
    "dob",
    "trans_num",
    "unix_time",
    "merch_lat",
    "merch_long",
    "is_fraud",
]


def find_csv_files() -> list:
    """Find transaction CSV files in the data directory."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
        log.warning(
            f"Data directory created at {DATA_DIR}. "
            f"Please download the Kaggle dataset and place CSV files there."
        )
        return []

    csv_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.csv")))
    # Filter for transaction-related CSVs (exclude other files)
    transaction_files = [
        f
        for f in csv_files
        if "fraud" in os.path.basename(f).lower()
        or "train" in os.path.basename(f).lower()
        or "test" in os.path.basename(f).lower()
    ]

    if not transaction_files:
        # Fall back to all CSVs if no specific pattern matches
        transaction_files = csv_files

    return transaction_files


def load_csv(file_path: str) -> pd.DataFrame:
    """
    Load and prepare a transaction CSV file.

    Args:
        file_path: Path to the CSV file.

    Returns:
        Cleaned DataFrame ready for Snowflake.
    """
    log.info(f"Reading CSV: {file_path}")
    df = pd.read_csv(file_path)

    log.info(f"Raw shape: {df.shape[0]} rows × {df.shape[1]} columns")

    # Standardize column names to match Snowflake table
    df.columns = [c.strip().lower() for c in df.columns]

    # Rename if needed (handle common Kaggle column name variations)
    column_mapping = {
        "unnamed: 0": "row_index",  # Drop index column if present
    }
    df = df.rename(columns=column_mapping)

    # Drop index column if present
    if "row_index" in df.columns:
        df = df.drop(columns=["row_index"])

    # Parse datetime → convert to string for Snowflake binding compatibility
    if "trans_date_trans_time" in df.columns:
        df["trans_date_trans_time"] = pd.to_datetime(
            df["trans_date_trans_time"], errors="coerce"
        ).dt.strftime("%Y-%m-%d %H:%M:%S")

    # Parse date of birth → convert to string
    if "dob" in df.columns:
        df["dob"] = pd.to_datetime(
            df["dob"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")

    # Ensure only expected columns are present (in the right order)
    available_columns = [c for c in LOAD_COLUMNS if c in df.columns]
    df = df[available_columns]

    # Replace NaN with None for Snowflake compatibility
    df = df.where(pd.notna(df), None)

    log.info(f"Prepared shape: {df.shape[0]} rows × {df.shape[1]} columns")
    return df


def ingest_transactions():
    """Main ingestion function for transaction data."""
    log.info("=" * 60)
    log.info("Starting transaction data ingestion")
    log.info("=" * 60)

    # Find CSV files
    csv_files = find_csv_files()
    if not csv_files:
        log.error(
            f"No CSV files found in {DATA_DIR}. "
            f"Download the dataset from: "
            f"https://www.kaggle.com/datasets/kartik2112/fraud-detection"
        )
        return

    log.info(f"Found {len(csv_files)} CSV file(s): {[os.path.basename(f) for f in csv_files]}")

    with get_snowflake_connection(
        schema=RAW_TRANSACTIONS_SCHEMA
    ) as conn:
        # Ensure target table exists
        execute_query(conn, CREATE_TABLE_SQL)
        log.info(f"Table {TABLE_NAME} ready.")

        # Truncate for idempotent full reload
        execute_query(
            conn,
            f"TRUNCATE TABLE IF EXISTS {SNOWFLAKE_DATABASE}.{RAW_TRANSACTIONS_SCHEMA}.{TABLE_NAME}",
        )
        log.info("Table truncated for fresh load.")

        # Load each CSV file
        total_rows = 0
        for csv_file in csv_files:
            df = load_csv(csv_file)
            if not df.empty:
                rows = write_dataframe(
                    conn=conn,
                    df=df,
                    table_name=TABLE_NAME,
                    schema=RAW_TRANSACTIONS_SCHEMA,
                    database=SNOWFLAKE_DATABASE,
                )
                total_rows += rows

        log.info("=" * 60)
        log.info(f"✅ Transaction ingestion complete — {total_rows} total rows loaded")
        log.info("=" * 60)


if __name__ == "__main__":
    ingest_transactions()
