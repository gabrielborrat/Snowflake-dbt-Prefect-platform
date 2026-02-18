-- =============================================================================
-- Fact: Daily Prices
-- =============================================================================
-- Grain: One row per security per trading day
-- Source: stg_market_prices
-- Materialization: incremental (merge)
--
-- Conformed dimensions: dim_dates, dim_currencies
-- Domain dimensions: dim_securities
--
-- Calculated measures:
--   daily_return = (close - previous_close) / previous_close
--   Uses LAG() window function partitioned by ticker, ordered by date
-- =============================================================================

{{
    config(
        materialized='incremental',
        unique_key='price_key',
        incremental_strategy='merge',
        on_schema_change='sync_all_columns'
    )
}}

WITH

-- Step 1: Source data (with incremental filter)
src_prices AS (
    SELECT *
    FROM {{ ref('stg_market_prices') }}

    {% if is_incremental() %}
    WHERE _source_loaded_at > (SELECT MAX(_source_loaded_at) FROM {{ this }})
    {% endif %}
),

-- Step 2: Dimension lookups
dim_dates AS (
    SELECT date_key, date_day
    FROM {{ ref('dim_dates') }}
),

dim_securities AS (
    SELECT security_key, ticker_symbol, trading_currency
    FROM {{ ref('dim_securities') }}
    WHERE security_key != '-1'
),

dim_currencies AS (
    SELECT currency_key, currency_code
    FROM {{ ref('dim_currencies') }}
),

-- Step 3: Calculate daily return using LAG
with_return AS (
    SELECT
        p.*,
        LAG(p.close_price) OVER (
            PARTITION BY p.ticker_symbol
            ORDER BY p.price_date
        ) AS previous_close_price
    FROM src_prices p
),

-- Step 4: Build fact with foreign keys and measures
joined AS (
    SELECT
        -- Primary key
        {{ dbt_utils.generate_surrogate_key(['p.ticker_symbol', 'p.price_date']) }}  AS price_key,

        -- Foreign keys (conformed dimensions) — coalesce_key handles orphan facts
        {{ coalesce_key('dd.date_key') }}                         AS date_key,
        {{ coalesce_key('cur.currency_key') }}                    AS currency_key,

        -- Foreign keys (domain dimensions)
        {{ coalesce_key('ds.security_key') }}                     AS security_key,

        -- Degenerate dimension
        p.ticker_symbol,

        -- Measures — prices
        p.open_price,
        p.high_price,
        p.low_price,
        p.close_price,
        p.adjusted_close_price,
        p.volume,

        -- Calculated measure — daily return (safe_divide handles zero/null)
        {{ safe_divide(
            'p.close_price - p.previous_close_price',
            'p.previous_close_price',
            6
        ) }}                                                       AS daily_return,

        -- Context
        p.price_date,

        -- Metadata
        p._source_loaded_at

    FROM with_return p

    -- Join to conformed date dimension
    LEFT JOIN dim_dates dd
        ON p.price_date = dd.date_day

    -- Join to security dimension (also gives us trading_currency)
    LEFT JOIN dim_securities ds
        ON p.ticker_symbol = ds.ticker_symbol

    -- Join to currency dimension via security's trading currency
    LEFT JOIN dim_currencies cur
        ON ds.trading_currency = cur.currency_code
),

-- Step 5: Final output
final AS (
    SELECT * FROM joined
)

SELECT * FROM final
