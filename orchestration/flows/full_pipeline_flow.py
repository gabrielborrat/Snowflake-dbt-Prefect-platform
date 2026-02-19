"""
Full Pipeline Flow
------------------
Top-level Prefect flow that chains the entire data platform:
  1. Ingestion  (parallel: transactions + market prices + FX rates)
  2. dbt        (sequential: staging → snapshot → marts → test)
  3. Validation (cross-layer row count reconciliation)
  4. Summary    (duration, row counts, overall status)

Scheduled: Daily at 06:00 UTC (configured via flow.serve() in deploy.py)
"""

import time

from prefect import flow
from prefect.logging import get_run_logger

from orchestration.config import PIPELINE_TIMEOUT
from orchestration.flows.ingestion_flow import ingestion_flow
from orchestration.flows.dbt_flow import dbt_flow
from orchestration.tasks.validation_tasks import (
    validate_row_counts,
    log_pipeline_summary,
)


@flow(
    name="full-pipeline",
    timeout_seconds=PIPELINE_TIMEOUT,
    log_prints=True,
)
def full_pipeline_flow():
    """Run the complete MDS pipeline: ingest → transform → validate."""
    logger = get_run_logger()
    start_time = time.time()

    logger.info("=" * 60)
    logger.info("STARTING FULL PIPELINE")
    logger.info("=" * 60)

    # Stage 1: Ingestion (concurrent — 3 independent sources)
    logger.info("Stage 1/4 — Ingestion (parallel)")
    ingestion_flow()

    # Stage 2: dbt transformation (sequential — DAG order)
    logger.info("Stage 2/4 — dbt Transformation (sequential)")
    dbt_flow()

    # Stage 3: Validation (cross-layer reconciliation)
    logger.info("Stage 3/4 — Validation")
    counts = validate_row_counts()

    # Stage 4: Summary
    logger.info("Stage 4/4 — Pipeline Summary")
    log_pipeline_summary(counts, start_time)

    logger.info("FULL PIPELINE COMPLETE")


if __name__ == "__main__":
    full_pipeline_flow()
