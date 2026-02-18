-- =============================================================================
-- Fact: Transactions
-- =============================================================================
-- Grain: One row per credit card transaction
-- Source: stg_transactions
-- Materialization: incremental (merge) — 1.85M+ rows, full rebuild too expensive
--
-- Conformed dimensions: dim_dates, dim_currencies
-- Domain dimensions: dim_customers, dim_merchants
--
-- Incremental strategy:
--   On first run (--full-refresh): loads all data
--   On subsequent runs: only processes rows where _source_loaded_at > max(existing)
--   Merge on unique_key ensures idempotency (no duplicates on re-run)
-- =============================================================================

{{
    config(
        materialized='incremental',
        unique_key='transaction_key',
        incremental_strategy='merge',
        on_schema_change='sync_all_columns'
    )
}}

WITH

-- Step 1: Source data (with incremental filter)
src_transactions AS (
    SELECT *
    FROM {{ ref('stg_transactions') }}

    {% if is_incremental() %}
    WHERE _source_loaded_at > (SELECT MAX(_source_loaded_at) FROM {{ this }})
    {% endif %}
),

-- Step 2: Dimension lookups — join to get foreign keys
dim_dates AS (
    SELECT date_key, date_day
    FROM {{ ref('dim_dates') }}
),

dim_customers AS (
    SELECT customer_key, card_number
    FROM {{ ref('dim_customers') }}
    WHERE customer_key != '-1'
),

dim_merchants AS (
    SELECT merchant_key, merchant_name
    FROM {{ ref('dim_merchants') }}
    WHERE merchant_key != '-1'
),

-- Transactions are in USD (Kaggle dataset is US-based credit card data)
dim_currencies AS (
    SELECT currency_key, currency_code
    FROM {{ ref('dim_currencies') }}
),

-- Step 3: Build fact with foreign keys and measures
joined AS (
    SELECT
        -- Primary key
        {{ dbt_utils.generate_surrogate_key(['t.trans_num']) }}  AS transaction_key,

        -- Foreign keys (conformed dimensions)
        COALESCE(dd.date_key, '-1')                              AS date_key,
        COALESCE(cur.currency_key, '-1')                         AS currency_key,

        -- Foreign keys (domain dimensions)
        COALESCE(dc.customer_key, '-1')                          AS customer_key,
        COALESCE(dm.merchant_key, '-1')                          AS merchant_key,

        -- Degenerate dimensions (kept on fact for drill-through)
        t.trans_num,
        t.card_number,

        -- Measures
        t.transaction_amount,
        t.is_fraud,

        -- Context
        t.transaction_at,
        t.transaction_date,
        t.category,

        -- Metadata
        t._source_loaded_at

    FROM src_transactions t

    -- Join to conformed date dimension
    LEFT JOIN dim_dates dd
        ON t.transaction_date = dd.date_day

    -- Join to customer dimension
    LEFT JOIN dim_customers dc
        ON t.card_number = dc.card_number

    -- Join to merchant dimension
    LEFT JOIN dim_merchants dm
        ON t.merchant_name = dm.merchant_name

    -- Join to currency dimension (USD — all transactions are US-based)
    LEFT JOIN dim_currencies cur
        ON cur.currency_code = 'USD'
),

-- Step 4: Final output
final AS (
    SELECT * FROM joined
)

SELECT * FROM final
