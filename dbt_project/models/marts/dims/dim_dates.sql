-- =============================================================================
-- Dimension: Dates (Date Spine)
-- =============================================================================
-- Grain: One row per calendar day
-- CONFORMED DIMENSION — shared across all fact tables
-- Generated using dbt_utils.date_spine
-- Range: 2019-01-01 to 2026-12-31 (configurable via dbt vars)
--
-- This is a role-playing dimension: the same date_key can be used for
-- transaction_date, price_date, rate_date, etc. in different fact tables.
-- =============================================================================

WITH

-- Step 1: Generate a continuous series of dates using dbt_utils
spine AS (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('" ~ var('date_spine_start') ~ "' as date)",
        end_date="cast('" ~ var('date_spine_end') ~ "' as date)"
    ) }}
),

-- Step 2: Rename the auto-generated column
date_series AS (
    SELECT
        date_day::DATE AS date_day
    FROM spine
),

-- Step 3: Enrich with calendar attributes
enriched AS (
    SELECT
        date_day,

        -- Day-level attributes
        DAYOFWEEK(date_day)                            AS day_of_week,        -- 0=Mon ... 6=Sun
        DAYNAME(date_day)                              AS day_of_week_name,   -- Mon, Tue, ...
        DAY(date_day)                                  AS day_of_month,
        DAYOFYEAR(date_day)                            AS day_of_year,

        -- Week-level attributes
        WEEKOFYEAR(date_day)                           AS week_of_year,

        -- Month-level attributes
        MONTH(date_day)                                AS month_number,
        MONTHNAME(date_day)                            AS month_name,         -- Jan, Feb, ...

        -- Quarter & Year
        QUARTER(date_day)                              AS quarter_number,
        YEAR(date_day)                                 AS year_number,

        -- Useful flags
        CASE
            WHEN DAYOFWEEK(date_day) IN (5, 6) THEN TRUE
            ELSE FALSE
        END                                            AS is_weekend,

        CASE
            WHEN DAY(date_day) = 1 THEN TRUE
            ELSE FALSE
        END                                            AS is_month_start,

        CASE
            WHEN date_day = LAST_DAY(date_day, 'month') THEN TRUE
            ELSE FALSE
        END                                            AS is_month_end,

        CASE
            WHEN MONTH(date_day) = 1 AND DAY(date_day) = 1 THEN TRUE
            ELSE FALSE
        END                                            AS is_year_start,

        CASE
            WHEN MONTH(date_day) = 12 AND DAY(date_day) = 31 THEN TRUE
            ELSE FALSE
        END                                            AS is_year_end,

        -- Trading day flag (exclude weekends — simplified; holidays not included)
        CASE
            WHEN DAYOFWEEK(date_day) NOT IN (5, 6) THEN TRUE
            ELSE FALSE
        END                                            AS is_trading_day

    FROM date_series
),

-- Step 4: Add surrogate key
final AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['date_day']) }}  AS date_key,
        *
    FROM enriched
)

SELECT * FROM final
