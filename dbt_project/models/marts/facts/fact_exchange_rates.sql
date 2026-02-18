-- =============================================================================
-- Fact: Exchange Rates
-- =============================================================================
-- Grain: One row per currency pair per day
-- Source: stg_exchange_rates
-- Materialization: incremental (merge)
--
-- Conformed dimensions: dim_dates, dim_currencies (role-playing: base + target)
-- Bridge fact enabling cross-domain currency conversion analysis
--
-- Calculated measures:
--   rate_change = today's rate - yesterday's rate (per pair)
--   Uses LAG() window function partitioned by currency pair, ordered by date
-- =============================================================================

{{
    config(
        materialized='incremental',
        unique_key='rate_key',
        incremental_strategy='merge',
        on_schema_change='sync_all_columns'
    )
}}

WITH

-- Step 1: Source data (with incremental filter)
src_rates AS (
    SELECT *
    FROM {{ ref('stg_exchange_rates') }}

    {% if is_incremental() %}
    WHERE _source_loaded_at > (SELECT MAX(_source_loaded_at) FROM {{ this }})
    {% endif %}
),

-- Step 2: Dimension lookups
dim_dates AS (
    SELECT date_key, date_day
    FROM {{ ref('dim_dates') }}
),

dim_currencies AS (
    SELECT currency_key, currency_code
    FROM {{ ref('dim_currencies') }}
),

-- Step 3: Calculate day-over-day rate change using LAG
with_change AS (
    SELECT
        r.*,
        LAG(r.exchange_rate) OVER (
            PARTITION BY r.base_currency, r.target_currency
            ORDER BY r.rate_date
        ) AS previous_rate
    FROM src_rates r
),

-- Step 4: Build fact with foreign keys and measures
joined AS (
    SELECT
        -- Primary key
        {{ dbt_utils.generate_surrogate_key(['r.base_currency', 'r.target_currency', 'r.rate_date']) }}  AS rate_key,

        -- Foreign keys (conformed dimensions) — coalesce_key handles orphan facts
        {{ coalesce_key('dd.date_key') }}                         AS date_key,

        -- Role-playing currency dimension: base and target
        {{ coalesce_key('cur_base.currency_key') }}               AS base_currency_key,
        {{ coalesce_key('cur_target.currency_key') }}             AS target_currency_key,

        -- Degenerate dimensions
        r.base_currency,
        r.target_currency,

        -- Measures
        r.exchange_rate,

        -- Calculated measure — day-over-day change (safe subtraction, NULL if no previous)
        CASE
            WHEN r.previous_rate IS NOT NULL
            THEN ROUND(r.exchange_rate - r.previous_rate, 6)
            ELSE NULL
        END                                                      AS rate_change,

        -- Context
        r.rate_date,

        -- Metadata
        r._source_loaded_at

    FROM with_change r

    -- Join to conformed date dimension
    LEFT JOIN dim_dates dd
        ON r.rate_date = dd.date_day

    -- Join to currency dimension for BASE currency (role-playing)
    LEFT JOIN dim_currencies cur_base
        ON r.base_currency = cur_base.currency_code

    -- Join to currency dimension for TARGET currency (role-playing)
    LEFT JOIN dim_currencies cur_target
        ON r.target_currency = cur_target.currency_code
),

-- Step 5: Final output
final AS (
    SELECT * FROM joined
)

SELECT * FROM final
