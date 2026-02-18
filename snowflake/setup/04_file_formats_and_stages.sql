-- =============================================================================
-- 04 — File Formats & Stages
-- =============================================================================
-- Run as: SYSADMIN
-- Purpose: Create file formats for data ingestion and internal stages.
--
-- File formats:
--   CSV_FORMAT  → For Kaggle CSV file ingestion (transactions)
--   JSON_FORMAT → For API response storage if needed
-- =============================================================================

USE ROLE SYSADMIN;

-- -----------------------------------------------------------------------------
-- CSV File Format (for Kaggle transaction data)
-- -----------------------------------------------------------------------------
CREATE FILE FORMAT IF NOT EXISTS RAW.TRANSACTIONS.CSV_FORMAT
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('', 'NULL', 'null', 'None')
    EMPTY_FIELD_AS_NULL = TRUE
    TRIM_SPACE = TRUE
    ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
    COMMENT = 'CSV format for Kaggle transaction data ingestion';

-- -----------------------------------------------------------------------------
-- JSON File Format (for API responses if needed)
-- -----------------------------------------------------------------------------
CREATE FILE FORMAT IF NOT EXISTS RAW.MARKET_DATA.JSON_FORMAT
    TYPE = 'JSON'
    STRIP_OUTER_ARRAY = TRUE
    COMMENT = 'JSON format for API response data';

-- -----------------------------------------------------------------------------
-- Internal Stage (optional — for file-based uploads)
-- -----------------------------------------------------------------------------
CREATE STAGE IF NOT EXISTS RAW.TRANSACTIONS.TRANSACTIONS_STAGE
    FILE_FORMAT = RAW.TRANSACTIONS.CSV_FORMAT
    COMMENT = 'Internal stage for transaction CSV file uploads';

-- -----------------------------------------------------------------------------
-- Verification
-- -----------------------------------------------------------------------------
SHOW FILE FORMATS IN DATABASE RAW;
SHOW STAGES IN SCHEMA RAW.TRANSACTIONS;
