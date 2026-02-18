"""
Snowflake Connector Utility
----------------------------
Reusable connection manager for Snowflake.
Provides context-managed connections and helper methods
for loading pandas DataFrames into Snowflake tables.
"""

from contextlib import contextmanager
import snowflake.connector
import pandas as pd
from ingestion.config import (
    SNOWFLAKE_ACCOUNT,
    SNOWFLAKE_USER,
    SNOWFLAKE_PASSWORD,
    SNOWFLAKE_ROLE,
    SNOWFLAKE_WAREHOUSE,
    SNOWFLAKE_DATABASE,
    BATCH_SIZE,
)
from ingestion.utils.logging_config import setup_logger

log = setup_logger("snowflake_connector")


@contextmanager
def get_snowflake_connection(
    role: str = None,
    warehouse: str = None,
    database: str = None,
    schema: str = None,
):
    """
    Context manager for Snowflake connections.

    Args:
        role: Snowflake role (default from config).
        warehouse: Snowflake warehouse (default from config).
        database: Snowflake database (default from config).
        schema: Snowflake schema (optional).

    Yields:
        Active Snowflake connection.
    """
    conn = None
    try:
        conn = snowflake.connector.connect(
            account=SNOWFLAKE_ACCOUNT,
            user=SNOWFLAKE_USER,
            password=SNOWFLAKE_PASSWORD,
            role=role or SNOWFLAKE_ROLE,
            warehouse=warehouse or SNOWFLAKE_WAREHOUSE,
            database=database or SNOWFLAKE_DATABASE,
            schema=schema,
        )
        log.info(
            f"Connected to Snowflake — role={role or SNOWFLAKE_ROLE}, "
            f"warehouse={warehouse or SNOWFLAKE_WAREHOUSE}, "
            f"database={database or SNOWFLAKE_DATABASE}"
            f"{f', schema={schema}' if schema else ''}"
        )
        yield conn
    except Exception as e:
        log.error(f"Snowflake connection failed: {e}")
        raise
    finally:
        if conn:
            conn.close()
            log.info("Snowflake connection closed.")


def execute_query(conn, query: str, params: tuple = None) -> list:
    """
    Execute a SQL query and return results.

    Args:
        conn: Active Snowflake connection.
        query: SQL query string.
        params: Optional query parameters.

    Returns:
        List of result rows.
    """
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        results = cursor.fetchall()
        log.debug(f"Query executed — {cursor.rowcount} rows returned.")
        return results
    finally:
        cursor.close()


def write_dataframe(
    conn,
    df: pd.DataFrame,
    table_name: str,
    schema: str,
    database: str = None,
    mode: str = "append",
) -> int:
    """
    Write a pandas DataFrame to a Snowflake table using batch inserts.

    Args:
        conn: Active Snowflake connection.
        df: DataFrame to upload.
        table_name: Target table name.
        schema: Target schema name.
        database: Target database (default from config).
        mode: 'append' or 'truncate' (truncate clears table first).

    Returns:
        Number of rows inserted.
    """
    if df.empty:
        log.warning(f"Empty DataFrame — skipping write to {schema}.{table_name}")
        return 0

    db = database or SNOWFLAKE_DATABASE
    fqn = f"{db}.{schema}.{table_name}"
    cursor = conn.cursor()

    try:
        # Truncate if requested
        if mode == "truncate":
            cursor.execute(f"TRUNCATE TABLE IF EXISTS {fqn}")
            log.info(f"Truncated {fqn}")

        # Build INSERT statement
        columns = ", ".join(df.columns)
        placeholders = ", ".join(["%s"] * len(df.columns))
        insert_sql = f"INSERT INTO {fqn} ({columns}) VALUES ({placeholders})"

        # Batch insert
        rows = [tuple(row) for row in df.itertuples(index=False, name=None)]
        total_inserted = 0

        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            cursor.executemany(insert_sql, batch)
            total_inserted += len(batch)
            log.info(
                f"Inserted batch {i // BATCH_SIZE + 1} — "
                f"{len(batch)} rows ({total_inserted}/{len(rows)} total)"
            )

        log.info(f"✅ Write complete — {total_inserted} rows → {fqn}")
        return total_inserted

    except Exception as e:
        log.error(f"Write failed to {fqn}: {e}")
        raise
    finally:
        cursor.close()


def merge_dataframe(
    conn,
    df: pd.DataFrame,
    table_name: str,
    schema: str,
    database: str = None,
    merge_keys: list = None,
) -> int:
    """
    Upsert a DataFrame into Snowflake using a MERGE statement.
    Creates a temp table, loads data, then merges into target.

    Args:
        conn: Active Snowflake connection.
        df: DataFrame to upsert.
        table_name: Target table name.
        schema: Target schema name.
        database: Target database (default from config).
        merge_keys: List of column names to match on.

    Returns:
        Number of rows processed.
    """
    if df.empty:
        log.warning(f"Empty DataFrame — skipping merge to {schema}.{table_name}")
        return 0

    if not merge_keys:
        raise ValueError("merge_keys must be provided for MERGE operations.")

    db = database or SNOWFLAKE_DATABASE
    fqn = f"{db}.{schema}.{table_name}"
    temp_table = f"{fqn}_temp_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}"
    cursor = conn.cursor()

    try:
        # Step 1: Create temp table with same structure
        cursor.execute(f"CREATE TEMPORARY TABLE {temp_table} LIKE {fqn}")
        log.info(f"Created temp table {temp_table}")

        # Step 2: Load data into temp table
        columns = ", ".join(df.columns)
        placeholders = ", ".join(["%s"] * len(df.columns))
        insert_sql = f"INSERT INTO {temp_table} ({columns}) VALUES ({placeholders})"

        rows = [tuple(row) for row in df.itertuples(index=False, name=None)]
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            cursor.executemany(insert_sql, batch)

        log.info(f"Loaded {len(rows)} rows into temp table")

        # Step 3: MERGE into target
        join_condition = " AND ".join(
            [f"target.{k} = source.{k}" for k in merge_keys]
        )

        # Update all non-key columns
        non_key_columns = [c for c in df.columns if c not in merge_keys]
        update_set = ", ".join(
            [f"target.{c} = source.{c}" for c in non_key_columns]
        )

        insert_columns = ", ".join(df.columns)
        insert_values = ", ".join([f"source.{c}" for c in df.columns])

        merge_sql = f"""
            MERGE INTO {fqn} AS target
            USING {temp_table} AS source
            ON {join_condition}
            WHEN MATCHED THEN UPDATE SET {update_set}
            WHEN NOT MATCHED THEN INSERT ({insert_columns}) VALUES ({insert_values})
        """

        cursor.execute(merge_sql)
        log.info(f"✅ Merge complete — {len(rows)} rows processed → {fqn}")

        # Step 4: Drop temp table
        cursor.execute(f"DROP TABLE IF EXISTS {temp_table}")

        return len(rows)

    except Exception as e:
        log.error(f"Merge failed to {fqn}: {e}")
        cursor.execute(f"DROP TABLE IF EXISTS {temp_table}")
        raise
    finally:
        cursor.close()
