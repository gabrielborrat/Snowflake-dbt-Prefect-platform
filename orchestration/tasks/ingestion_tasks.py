"""
Ingestion Tasks
----------------
@task-decorated wrappers around the ingestion scripts.
Each source is isolated as its own Prefect task with differentiated
retry/timeout config based on failure risk profile.

- CSV (transactions): local file, low failure risk → 1 retry
- API (market prices, exchange rates): external dependency → 3 retries
"""

from prefect import task

from ingestion.sources.ingest_transactions import (
    ingest_transactions as _ingest_transactions,
)
from ingestion.sources.ingest_market_prices import (
    ingest_market_prices as _ingest_market_prices,
)
from ingestion.sources.ingest_exchange_rates import (
    ingest_exchange_rates as _ingest_exchange_rates,
)
from orchestration.config import (
    LOCAL_TASK_RETRIES,
    LOCAL_TASK_RETRY_DELAY,
    LOCAL_TASK_TIMEOUT,
    API_TASK_RETRIES,
    API_TASK_RETRY_DELAY,
    API_TASK_TIMEOUT,
    TAGS_INGESTION_CSV,
    TAGS_INGESTION_API,
)


@task(
    name="ingest-transactions",
    retries=LOCAL_TASK_RETRIES,
    retry_delay_seconds=LOCAL_TASK_RETRY_DELAY,
    timeout_seconds=LOCAL_TASK_TIMEOUT,
    tags=TAGS_INGESTION_CSV,
)
def ingest_transactions_task():
    """Load credit card transactions from CSV into Snowflake RAW."""
    _ingest_transactions()
    return {"source": "transactions", "status": "completed"}


@task(
    name="ingest-market-prices",
    retries=API_TASK_RETRIES,
    retry_delay_seconds=API_TASK_RETRY_DELAY,
    timeout_seconds=API_TASK_TIMEOUT,
    tags=TAGS_INGESTION_API,
)
def ingest_market_prices_task():
    """Load daily stock prices from Yahoo Finance API into Snowflake RAW."""
    _ingest_market_prices()
    return {"source": "market_prices", "status": "completed"}


@task(
    name="ingest-exchange-rates",
    retries=API_TASK_RETRIES,
    retry_delay_seconds=API_TASK_RETRY_DELAY,
    timeout_seconds=API_TASK_TIMEOUT,
    tags=TAGS_INGESTION_API,
)
def ingest_exchange_rates_task():
    """Load daily FX rates from frankfurter.app API into Snowflake RAW."""
    _ingest_exchange_rates()
    return {"source": "exchange_rates", "status": "completed"}
