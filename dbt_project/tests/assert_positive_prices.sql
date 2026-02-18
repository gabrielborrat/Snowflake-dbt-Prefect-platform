-- =============================================================================
-- Singular Test: Positive Close Prices
-- =============================================================================
-- Business rule: All close prices must be strictly positive.
-- A stock cannot have a zero or negative closing price — this would indicate
-- corrupt source data or a transformation bug.
--
-- Layer: fact_daily_prices (Gold)
-- =============================================================================

SELECT
    price_key,
    ticker_symbol,
    price_date,
    close_price
FROM {{ ref('fact_daily_prices') }}
WHERE close_price <= 0
   OR close_price IS NULL

