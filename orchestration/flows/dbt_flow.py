"""
dbt Flow
--------
Prefect flow that runs dbt commands in strict dependency order.

Sequential execution: staging → snapshot → marts → test.
This order respects dbt's DAG: staging models must exist before
marts can ref() them, and snapshots capture staging data before
marts consume it.
"""

from prefect import flow
from prefect.logging import get_run_logger

from orchestration.tasks.dbt_tasks import (
    dbt_run_staging,
    dbt_snapshot,
    dbt_run_marts,
    dbt_test,
)


@flow(name="dbt-flow", log_prints=True)
def dbt_flow():
    """Run the full dbt transformation pipeline sequentially."""
    logger = get_run_logger()

    logger.info("Step 1/4 — dbt run staging (Silver layer)")
    dbt_run_staging()

    logger.info("Step 2/4 — dbt snapshot (SCD2)")
    dbt_snapshot()

    logger.info("Step 3/4 — dbt run marts (Gold layer)")
    dbt_run_marts()

    logger.info("Step 4/4 — dbt test (validation)")
    dbt_test()

    logger.info("dbt flow complete — all 4 steps passed")


if __name__ == "__main__":
    dbt_flow()
