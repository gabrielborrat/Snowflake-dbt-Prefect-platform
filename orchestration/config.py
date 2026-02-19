"""
Orchestration Configuration
----------------------------
Centralized settings for Prefect flows and tasks.
Keeps retry counts, timeouts, schedules, and paths
out of flow/task logic for easy tuning.
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DBT_PROJECT_DIR = PROJECT_ROOT / "dbt_project"

# ---------------------------------------------------------------------------
# Retry & timeout defaults (seconds)
# ---------------------------------------------------------------------------
# API-dependent ingestion tasks: higher retry count for transient failures
API_TASK_RETRIES = 3
API_TASK_RETRY_DELAY = 60
API_TASK_TIMEOUT = 1800  # 30 min

# Local / file-based tasks: low failure risk
LOCAL_TASK_RETRIES = 1
LOCAL_TASK_RETRY_DELAY = 30
LOCAL_TASK_TIMEOUT = 1800

# dbt tasks
DBT_TASK_RETRIES = 1
DBT_TASK_RETRY_DELAY = 30
DBT_RUN_TIMEOUT = 1800   # staging + marts
DBT_TEST_TIMEOUT = 600
DBT_SNAPSHOT_TIMEOUT = 600

# dbt test tasks should NOT be retried — failure is informational
DBT_TEST_RETRIES = 0

# Full pipeline flow
PIPELINE_TIMEOUT = 7200  # 2 hours

# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------
PIPELINE_CRON = "0 6 * * *"  # daily at 06:00 UTC

# ---------------------------------------------------------------------------
# dbt CLI settings
# ---------------------------------------------------------------------------
DBT_PROFILES_DIR = str(DBT_PROJECT_DIR)
DBT_TARGET = os.getenv("DBT_TARGET", "dev")

# ---------------------------------------------------------------------------
# Tags (for Prefect UI filtering)
# ---------------------------------------------------------------------------
TAGS_INGESTION = ["ingestion"]
TAGS_INGESTION_API = ["ingestion", "api"]
TAGS_INGESTION_CSV = ["ingestion", "csv"]
TAGS_DBT = ["dbt", "transformation"]
TAGS_VALIDATION = ["validation"]
