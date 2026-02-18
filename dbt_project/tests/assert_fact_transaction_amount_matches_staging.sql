-- =============================================================================
-- Singular Test: Fact Transaction Row Count Matches Staging
-- =============================================================================
-- Business rule: The number of rows in fact_transactions must equal the number
-- of rows in stg_transactions. If they diverge, it means either:
--   - The incremental merge dropped rows (FK join issue)
--   - A duplicate was introduced
--   - The incremental filter skipped data
--
-- This is a "row count sanity check" — a lightweight data reconciliation test
-- that catches serious ETL issues at the mart level.
--
-- The test returns one row (with the two counts) if they differ → FAIL.
-- If counts match → 0 rows → PASS.
-- =============================================================================

WITH

fact_count AS (
    SELECT COUNT(*) AS cnt
    FROM {{ ref('fact_transactions') }}
),

staging_count AS (
    SELECT COUNT(*) AS cnt
    FROM {{ ref('stg_transactions') }}
)

SELECT
    f.cnt   AS fact_row_count,
    s.cnt   AS staging_row_count,
    f.cnt - s.cnt AS difference
FROM fact_count f
CROSS JOIN staging_count s
WHERE f.cnt != s.cnt

