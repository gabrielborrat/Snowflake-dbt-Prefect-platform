-- =============================================================================
-- Staging: Market Prices
-- =============================================================================
-- Source: RAW.MARKET_DATA.DAILY_PRICES
-- Grain:  One row per ticker per trading day
-- Pattern: src_data → renamed → cleaned → final
--
-- Transformations applied:
--   - Rename columns to project conventions
--   - Cast prices to DECIMAL(12,4) for precision
--   - Cast volume to BIGINT
--   - UPPER(ticker) for consistency
--   - Passthrough _loaded_at as _source_loaded_at
-- =============================================================================

WITH

-- Step 1: Pull raw data from source (no changes)
src_data AS (
    SELECT *
    FROM {{ source('raw_market_data', 'daily_prices') }}
),

-- Step 2: Rename columns to project naming conventions
renamed AS (
    SELECT
        ticker                     AS ticker_symbol,
        date                       AS price_date,
        open                       AS open_price,
        high                       AS high_price,
        low                        AS low_price,
        close                      AS close_price,
        adj_close                  AS adjusted_close_price,
        volume,
        _loaded_at                 AS _source_loaded_at
    FROM src_data
),

-- Step 3: Clean — cast types, validate, standardize
cleaned AS (
    SELECT
        UPPER(TRIM(ticker_symbol))                     AS ticker_symbol,
        price_date,
        open_price::DECIMAL(12,4)                      AS open_price,
        high_price::DECIMAL(12,4)                      AS high_price,
        low_price::DECIMAL(12,4)                       AS low_price,
        close_price::DECIMAL(12,4)                     AS close_price,
        adjusted_close_price::DECIMAL(12,4)            AS adjusted_close_price,
        volume::BIGINT                                 AS volume,
        _source_loaded_at
    FROM renamed
),

-- Step 4: Final output
final AS (
    SELECT * FROM cleaned
)

SELECT * FROM final
