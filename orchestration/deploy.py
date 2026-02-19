"""
Deployment Script
-----------------
Registers the full MDS pipeline as a Prefect deployment with a daily
cron schedule.  Running this script starts a long-lived process that
keeps the deployment alive and triggers the flow on schedule.

Usage:
    python -m orchestration.deploy          # foreground (Ctrl+C to stop)

The deployment will also appear in the Prefect UI under the
Deployments tab, where it can be triggered manually via "Quick Run".
"""

from orchestration.config import PIPELINE_CRON
from orchestration.flows.full_pipeline_flow import full_pipeline_flow


def main():
    full_pipeline_flow.serve(
        name="daily-mds-pipeline",
        cron=PIPELINE_CRON,
        tags=["production", "daily"],
        description=(
            "Full MDS pipeline: ingest → transform → validate. "
            "Runs daily at 06:00 UTC."
        ),
    )


if __name__ == "__main__":
    main()
