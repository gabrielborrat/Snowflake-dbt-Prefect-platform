-- =============================================================================
-- Singular Test: No Future Transactions
-- =============================================================================
-- Business rule: No transaction should have a date in the future.
-- If any row is returned, the test FAILS — indicating a data quality issue
-- (e.g., bad source data, timezone miscalculation, or ingestion error).
--
-- Layer: fact_transactions (Gold)
-- =============================================================================

SELECT
    transaction_key,
    trans_num,
    transaction_date,
    _source_loaded_at
FROM {{ ref('fact_transactions') }}
WHERE transaction_date > CURRENT_DATE()

