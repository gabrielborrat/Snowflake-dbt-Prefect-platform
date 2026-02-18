-- =============================================================================
-- Staging: Exchange Rates
-- =============================================================================
-- Source: RAW.EXCHANGE_RATES.DAILY_RATES
-- Grain:  One row per currency pair per day
-- Pattern: src_data → renamed → cleaned → final
--
-- Transformations applied:
--   - Rename columns to project conventions
--   - Cast rate to DECIMAL(12,6) for precision
--   - UPPER currency codes for consistency
--   - Passthrough _loaded_at as _source_loaded_at
-- =============================================================================

WITH

-- Step 1: Pull raw data from source (no changes)
src_data AS (
    SELECT *
    FROM {{ source('raw_exchange_rates', 'daily_rates') }}
),

-- Step 2: Rename columns to project naming conventions
renamed AS (
    SELECT
        base_currency,
        target_currency,
        date                       AS rate_date,
        rate                       AS exchange_rate,
        _loaded_at                 AS _source_loaded_at
    FROM src_data
),

-- Step 3: Clean — cast types, standardize
cleaned AS (
    SELECT
        UPPER(TRIM(base_currency))                     AS base_currency,
        UPPER(TRIM(target_currency))                   AS target_currency,
        rate_date,
        exchange_rate::DECIMAL(12,6)                   AS exchange_rate,
        _source_loaded_at
    FROM renamed
),

-- Step 4: Final output
final AS (
    SELECT * FROM cleaned
)

SELECT * FROM final
