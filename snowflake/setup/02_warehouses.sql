-- =============================================================================
-- 02 — Warehouses
-- =============================================================================
-- Run as: SYSADMIN (or ACCOUNTADMIN)
-- Purpose: Create compute warehouses with separation of concerns.
--
-- Strategy:
--   INGESTION_WH   → Used by Python ingestion scripts
--   TRANSFORM_WH   → Used by dbt for transformations
--   REPORTING_WH   → Used by Power BI for dashboard queries
--
-- Cost control:
--   - All warehouses are X-Small (1 credit/hour)
--   - Auto-suspend after 60 seconds of inactivity
--   - Auto-resume on query arrival
--   - No scaling (single cluster)
-- =============================================================================

USE ROLE SYSADMIN;

-- -----------------------------------------------------------------------------
-- Ingestion Warehouse
-- -----------------------------------------------------------------------------
CREATE WAREHOUSE IF NOT EXISTS INGESTION_WH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 1
    COMMENT = 'Compute for Python ingestion scripts — loads data into RAW';

-- -----------------------------------------------------------------------------
-- Transformation Warehouse
-- -----------------------------------------------------------------------------
CREATE WAREHOUSE IF NOT EXISTS TRANSFORM_WH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 1
    COMMENT = 'Compute for dbt transformations — staging and marts';

-- -----------------------------------------------------------------------------
-- Reporting Warehouse
-- -----------------------------------------------------------------------------
CREATE WAREHOUSE IF NOT EXISTS REPORTING_WH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 1
    COMMENT = 'Compute for Power BI dashboard queries — reads from MARTS';

-- -----------------------------------------------------------------------------
-- Verification
-- -----------------------------------------------------------------------------
SHOW WAREHOUSES;
