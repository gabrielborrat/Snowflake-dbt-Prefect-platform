"""
Ingestion Flow
--------------
Prefect flow that orchestrates all three ingestion sources.

Concurrency: transactions, market prices, and exchange rates write to
independent Snowflake tables, so they run in parallel via
ThreadPoolTaskRunner. A failure in one source does not block the others.
"""

from prefect import flow
from prefect.task_runners import ThreadPoolTaskRunner

from orchestration.tasks.ingestion_tasks import (
    ingest_transactions_task,
    ingest_market_prices_task,
    ingest_exchange_rates_task,
)


@flow(
    name="ingestion-flow",
    task_runner=ThreadPoolTaskRunner(max_workers=3),
    log_prints=True,
)
def ingestion_flow():
    """Run all ingestion sources concurrently."""
    tx_future = ingest_transactions_task.submit()
    mp_future = ingest_market_prices_task.submit()
    fx_future = ingest_exchange_rates_task.submit()

    results = [
        tx_future.result(),
        mp_future.result(),
        fx_future.result(),
    ]

    completed = [r["source"] for r in results if r and r.get("status") == "completed"]
    print(f"Ingestion complete — {len(completed)}/3 sources loaded: {completed}")
    return results


if __name__ == "__main__":
    ingestion_flow()
