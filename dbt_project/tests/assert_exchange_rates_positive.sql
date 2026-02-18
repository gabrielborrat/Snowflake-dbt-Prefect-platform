-- =============================================================================
-- Singular Test: Positive Exchange Rates
-- =============================================================================
-- Business rule: All exchange rates must be strictly positive.
-- A currency pair cannot have a zero or negative rate — this would indicate
-- corrupt ECB data or a transformation bug.
--
-- Layer: fact_exchange_rates (Gold)
-- =============================================================================

SELECT
    rate_key,
    base_currency,
    target_currency,
    rate_date,
    exchange_rate
FROM {{ ref('fact_exchange_rates') }}
WHERE exchange_rate <= 0
   OR exchange_rate IS NULL

