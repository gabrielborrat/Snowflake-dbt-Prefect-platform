-- =============================================================================
-- Cost Monitoring Queries
-- =============================================================================
-- Run as: ACCOUNTADMIN
-- Purpose: Monitor Snowflake credit consumption during the trial period.
--
-- Trial budget: $400 in credits
-- Expected usage: $5–15 total for this project (XS warehouses, auto-suspend)
--
-- Run these periodically to stay aware of costs.
-- =============================================================================

USE ROLE ACCOUNTADMIN;

-- -----------------------------------------------------------------------------
-- 1. Total credits used (all time)
-- -----------------------------------------------------------------------------
SELECT
    SUM(credits_used) AS total_credits_used,
    SUM(credits_used) * 3.00 AS estimated_cost_usd  -- ~$3/credit on Enterprise
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY;

-- -----------------------------------------------------------------------------
-- 2. Credits used per warehouse (identify cost drivers)
-- -----------------------------------------------------------------------------
SELECT
    warehouse_name,
    SUM(credits_used) AS credits_used,
    SUM(credits_used) * 3.00 AS estimated_cost_usd,
    COUNT(*) AS num_intervals
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
GROUP BY warehouse_name
ORDER BY credits_used DESC;

-- -----------------------------------------------------------------------------
-- 3. Daily credit consumption (trend)
-- -----------------------------------------------------------------------------
SELECT
    DATE_TRUNC('day', start_time) AS usage_date,
    warehouse_name,
    SUM(credits_used) AS credits_used
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
GROUP BY usage_date, warehouse_name
ORDER BY usage_date DESC;

-- -----------------------------------------------------------------------------
-- 4. Credits remaining (approximate)
-- -----------------------------------------------------------------------------
-- Trial gives $400 in credits. Check how much is left.
SELECT
    400.00 - SUM(credits_used) * 3.00 AS estimated_remaining_usd,
    SUM(credits_used) AS total_credits_used
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY;

-- -----------------------------------------------------------------------------
-- 5. Warehouse auto-suspend verification
-- -----------------------------------------------------------------------------
-- Ensure all warehouses have auto-suspend configured
SELECT
    name AS warehouse_name,
    size AS warehouse_size,
    auto_suspend AS auto_suspend_seconds,
    auto_resume,
    CASE
        WHEN auto_suspend <= 60 THEN '✅ Good'
        WHEN auto_suspend <= 300 THEN '⚠️ Consider lowering'
        ELSE '❌ Too high — costs risk'
    END AS suspend_status
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSES
WHERE deleted_on IS NULL;

-- -----------------------------------------------------------------------------
-- 6. Query history (recent expensive queries)
-- -----------------------------------------------------------------------------
SELECT
    query_id,
    query_text,
    warehouse_name,
    execution_status,
    total_elapsed_time / 1000 AS elapsed_seconds,
    credits_used_cloud_services,
    start_time
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE start_time >= DATEADD('day', -7, CURRENT_TIMESTAMP())
ORDER BY total_elapsed_time DESC
LIMIT 20;
