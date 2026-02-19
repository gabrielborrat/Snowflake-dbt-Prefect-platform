"""
dbt Tasks
---------
@task-decorated wrappers around dbt CLI commands.

Uses subprocess.run() rather than dbt's internal Python API because
the CLI is the stable, supported contract. Same approach used by
Airflow's BashOperator and Dagster's dbt_cli_resource.

Each dbt command is a separate task so Prefect tracks them independently
in the UI and applies per-task retry/timeout settings.
"""

import subprocess
import os

from prefect import task
from prefect.logging import get_run_logger
from dotenv import dotenv_values

from orchestration.config import (
    DBT_PROJECT_DIR,
    DBT_PROFILES_DIR,
    DBT_TASK_RETRIES,
    DBT_TASK_RETRY_DELAY,
    DBT_RUN_TIMEOUT,
    DBT_TEST_TIMEOUT,
    DBT_TEST_RETRIES,
    DBT_SNAPSHOT_TIMEOUT,
    TAGS_DBT,
)

PROJECT_ROOT = DBT_PROJECT_DIR.parent


def _load_env_vars() -> dict:
    """Build an env dict with .env variables loaded for dbt subprocess.

    Uses python-dotenv (dotenv_values) to correctly parse .env files,
    including handling inline comments and quoted values.
    """
    env = os.environ.copy()
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        parsed = dotenv_values(env_path)
        env.update(parsed)
    return env


def _run_dbt_command(args: list[str], description: str) -> str:
    """
    Execute a dbt CLI command via subprocess.

    Args:
        args: dbt command arguments (e.g. ["run", "--select", "staging"]).
        description: Human-readable label for logging.

    Returns:
        stdout output from the command.

    Raises:
        subprocess.CalledProcessError: if dbt exits with non-zero code.
    """
    logger = get_run_logger()
    cmd = ["dbt"] + args + ["--profiles-dir", str(DBT_PROFILES_DIR)]

    logger.info(f"Running: {' '.join(cmd)}")
    logger.info(f"Working directory: {DBT_PROJECT_DIR}")

    result = subprocess.run(
        cmd,
        cwd=str(DBT_PROJECT_DIR),
        capture_output=True,
        text=True,
        env=_load_env_vars(),
    )

    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            logger.info(f"[dbt] {line}")

    if result.returncode != 0:
        if result.stderr:
            for line in result.stderr.strip().split("\n"):
                logger.error(f"[dbt stderr] {line}")
        result.check_returncode()

    logger.info(f"{description} completed successfully")
    return result.stdout


@task(
    name="dbt-run-staging",
    retries=DBT_TASK_RETRIES,
    retry_delay_seconds=DBT_TASK_RETRY_DELAY,
    timeout_seconds=DBT_RUN_TIMEOUT,
    tags=TAGS_DBT,
)
def dbt_run_staging() -> str:
    """Run dbt models for the staging (Silver) layer."""
    return _run_dbt_command(
        ["run", "--select", "staging"],
        "dbt run staging",
    )


@task(
    name="dbt-snapshot",
    retries=DBT_TASK_RETRIES,
    retry_delay_seconds=DBT_TASK_RETRY_DELAY,
    timeout_seconds=DBT_SNAPSHOT_TIMEOUT,
    tags=TAGS_DBT,
)
def dbt_snapshot() -> str:
    """Run dbt snapshots (SCD2 capture)."""
    return _run_dbt_command(
        ["snapshot"],
        "dbt snapshot",
    )


@task(
    name="dbt-run-marts",
    retries=DBT_TASK_RETRIES,
    retry_delay_seconds=DBT_TASK_RETRY_DELAY,
    timeout_seconds=DBT_RUN_TIMEOUT,
    tags=TAGS_DBT,
)
def dbt_run_marts() -> str:
    """Run dbt models for the marts (Gold) layer."""
    return _run_dbt_command(
        ["run", "--select", "marts"],
        "dbt run marts",
    )


@task(
    name="dbt-test",
    retries=DBT_TEST_RETRIES,
    timeout_seconds=DBT_TEST_TIMEOUT,
    tags=TAGS_DBT,
)
def dbt_test() -> str:
    """Run dbt tests. Not retried — failure is informational."""
    return _run_dbt_command(
        ["test"],
        "dbt test",
    )
