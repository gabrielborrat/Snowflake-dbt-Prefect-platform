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
    """Run the complete MDS pipeline: ingest → transform → validate.

    Flow-level error handling ensures the pipeline summary is always
    logged, even when a stage fails. This follows the "fail gracefully,
    log loudly" principle from Phase 2.
    """
    logger = get_run_logger()
    start_time = time.time()
    stage_results = {"ingestion": None, "dbt": None, "validation": None}

    logger.info("=" * 60)
    logger.info("STARTING FULL PIPELINE")
    logger.info("=" * 60)

    try:
        # Stage 1: Ingestion (concurrent — 3 independent sources)
        logger.info("Stage 1/4 — Ingestion (parallel)")
        ingestion_flow()
        stage_results["ingestion"] = "completed"
    except Exception as e:
        stage_results["ingestion"] = f"failed: {e}"
        logger.error(f"Stage 1 FAILED — Ingestion: {e}")
        logger.error("Skipping dbt transformation (no fresh data to transform)")
        _log_failure_summary(logger, stage_results, start_time)
        raise

    try:
        # Stage 2: dbt transformation (sequential — DAG order)
        logger.info("Stage 2/4 — dbt Transformation (sequential)")
        dbt_flow()
        stage_results["dbt"] = "completed"
    except Exception as e:
        stage_results["dbt"] = f"failed: {e}"
        logger.error(f"Stage 2 FAILED — dbt: {e}")
        logger.warning("Proceeding to validation with stale data")

    # Stage 3: Validation (runs even if dbt had issues)
    logger.info("Stage 3/4 — Validation")
    try:
        counts = validate_row_counts()
        stage_results["validation"] = "completed"
    except Exception as e:
        stage_results["validation"] = f"failed: {e}"
        logger.error(f"Stage 3 FAILED — Validation: {e}")
        counts = {"_reconciliation_passed": False}

    # Stage 4: Summary (always runs)
    logger.info("Stage 4/4 — Pipeline Summary")
    log_pipeline_summary(counts, start_time)

    if stage_results["dbt"] and "failed" in str(stage_results["dbt"]):
        raise RuntimeError(
            f"Pipeline completed with errors: {stage_results}"
        )

    logger.info("FULL PIPELINE COMPLETE")


def _log_failure_summary(logger, stage_results: dict, start_time: float):
    """Log a minimal summary when the pipeline fails early."""
    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    logger.error("=" * 60)
    logger.error("PIPELINE FAILED — EARLY EXIT")
    logger.error(f"  Duration: {minutes}m {seconds}s")
    for stage, result in stage_results.items():
        status = result or "not started"
        logger.error(f"  {stage:15}: {status}")
    logger.error("=" * 60)


if __name__ == "__main__":
    full_pipeline_flow()
