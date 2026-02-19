"""
Validation Tasks
-----------------
@task-decorated wrappers for cross-layer row count reconciliation
and pipeline summary logging.

These tasks run after ingestion + dbt to verify data integrity
across the RAW → STAGING → MARTS pipeline.
"""

import time
from prefect import task
from prefect.logging import get_run_logger

from ingestion.utils.snowflake_connector import get_snowflake_connection, execute_query
from orchestration.config import TAGS_VALIDATION

ROW_COUNT_QUERIES = {
    "RAW.TRANSACTIONS.CREDIT_CARD_TRANSACTIONS": "SELECT COUNT(*) FROM RAW.TRANSACTIONS.CREDIT_CARD_TRANSACTIONS",
    "RAW.MARKET_DATA.DAILY_PRICES": "SELECT COUNT(*) FROM RAW.MARKET_DATA.DAILY_PRICES",
    "RAW.EXCHANGE_RATES.DAILY_RATES": "SELECT COUNT(*) FROM RAW.EXCHANGE_RATES.DAILY_RATES",
    "ANALYTICS.STAGING.STG_TRANSACTIONS": "SELECT COUNT(*) FROM ANALYTICS.STAGING.STG_TRANSACTIONS",
    "ANALYTICS.STAGING.STG_MARKET_PRICES": "SELECT COUNT(*) FROM ANALYTICS.STAGING.STG_MARKET_PRICES",
    "ANALYTICS.STAGING.STG_EXCHANGE_RATES": "SELECT COUNT(*) FROM ANALYTICS.STAGING.STG_EXCHANGE_RATES",
    "ANALYTICS.MARTS.FACT_TRANSACTIONS": "SELECT COUNT(*) FROM ANALYTICS.MARTS.FACT_TRANSACTIONS",
    "ANALYTICS.MARTS.FACT_DAILY_PRICES": "SELECT COUNT(*) FROM ANALYTICS.MARTS.FACT_DAILY_PRICES",
    "ANALYTICS.MARTS.FACT_EXCHANGE_RATES": "SELECT COUNT(*) FROM ANALYTICS.MARTS.FACT_EXCHANGE_RATES",
    "ANALYTICS.MARTS.DIM_DATES": "SELECT COUNT(*) FROM ANALYTICS.MARTS.DIM_DATES",
    "ANALYTICS.MARTS.DIM_CUSTOMERS": "SELECT COUNT(*) FROM ANALYTICS.MARTS.DIM_CUSTOMERS",
    "ANALYTICS.MARTS.DIM_MERCHANTS": "SELECT COUNT(*) FROM ANALYTICS.MARTS.DIM_MERCHANTS",
    "ANALYTICS.MARTS.DIM_SECURITIES": "SELECT COUNT(*) FROM ANALYTICS.MARTS.DIM_SECURITIES",
    "ANALYTICS.MARTS.DIM_CURRENCIES": "SELECT COUNT(*) FROM ANALYTICS.MARTS.DIM_CURRENCIES",
}

RECONCILIATION_RULES = [
    {
        "name": "Transactions: staging dedup matches fact",
        "source": "ANALYTICS.STAGING.STG_TRANSACTIONS",
        "target": "ANALYTICS.MARTS.FACT_TRANSACTIONS",
    },
    {
        "name": "Market prices: staging matches fact",
        "source": "ANALYTICS.STAGING.STG_MARKET_PRICES",
        "target": "ANALYTICS.MARTS.FACT_DAILY_PRICES",
    },
    {
        "name": "Exchange rates: staging matches fact",
        "source": "ANALYTICS.STAGING.STG_EXCHANGE_RATES",
        "target": "ANALYTICS.MARTS.FACT_EXCHANGE_RATES",
    },
]


@task(
    name="validate-row-counts",
    timeout_seconds=120,
    tags=TAGS_VALIDATION,
)
def validate_row_counts() -> dict:
    """Query row counts across all layers and run reconciliation checks."""
    logger = get_run_logger()

    counts = {}
    with get_snowflake_connection(
        role="TRANSFORM_ROLE",
        warehouse="TRANSFORM_WH",
        database="ANALYTICS",
    ) as conn:
        for table, query in ROW_COUNT_QUERIES.items():
            try:
                result = execute_query(conn, query)
                counts[table] = result[0][0]
            except Exception as e:
                logger.warning(f"Could not query {table}: {e}")
                counts[table] = -1

    logger.info("=" * 60)
    logger.info("ROW COUNT VALIDATION")
    logger.info("=" * 60)

    for table, count in counts.items():
        layer = table.split(".")[0]
        logger.info(f"  [{layer:10}] {table:50} → {count:>12,} rows")

    logger.info("-" * 60)
    logger.info("RECONCILIATION CHECKS")
    logger.info("-" * 60)

    all_passed = True
    for rule in RECONCILIATION_RULES:
        src_count = counts.get(rule["source"], -1)
        tgt_count = counts.get(rule["target"], -1)
        passed = src_count == tgt_count and src_count >= 0
        status = "✅ PASS" if passed else "❌ FAIL"

        if not passed:
            all_passed = False

        logger.info(
            f"  {status} | {rule['name']} | "
            f"source={src_count:,} target={tgt_count:,}"
        )

    logger.info("=" * 60)
    counts["_reconciliation_passed"] = all_passed
    return counts


@task(
    name="log-pipeline-summary",
    timeout_seconds=30,
    tags=TAGS_VALIDATION,
)
def log_pipeline_summary(counts: dict, start_time: float) -> None:
    """Log a final pipeline summary with duration, row counts, and status."""
    logger = get_run_logger()
    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    reconciliation_passed = counts.get("_reconciliation_passed", False)

    logger.info("")
    logger.info("=" * 60)
    logger.info("PIPELINE SUMMARY")
    logger.info("=" * 60)
    logger.info(f"  Duration:        {minutes}m {seconds}s")
    logger.info(f"  Reconciliation:  {'✅ ALL CHECKS PASSED' if reconciliation_passed else '❌ SOME CHECKS FAILED'}")
    logger.info("")

    for table, count in counts.items():
        if table.startswith("_"):
            continue
        logger.info(f"  {table:50} → {count:>12,} rows")

    logger.info("=" * 60)
    overall = "COMPLETED" if reconciliation_passed else "COMPLETED WITH WARNINGS"
    logger.info(f"  Pipeline status: {overall}")
    logger.info("=" * 60)
