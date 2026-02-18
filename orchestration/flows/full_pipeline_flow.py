"""
Full Pipeline Flow
------------------
Prefect flow that chains the complete pipeline:
  1. Ingestion (parallel: transactions + market prices + FX rates)
  2. dbt run (staging → marts)
  3. dbt test (validation)
  4. Pipeline summary log

Scheduled: Daily at 06:00 UTC
Retries: 3 per ingestion task, 60s delay

Implementation: Phase 4
"""

# TODO: Implement in Phase 4

