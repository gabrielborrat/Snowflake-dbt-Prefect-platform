-- =============================================================================
-- Dimension: Currencies
-- =============================================================================
-- Grain: One row per currency
-- CONFORMED DIMENSION — shared across all fact tables
-- Source: seed (currency_codes.csv)
--
-- Includes a default record (key = '-1') for orphan fact handling.
-- =============================================================================

WITH

-- Step 1: Pull from seed
src_seed AS (
    SELECT
        currency_code,
        currency_name,
        region
    FROM {{ ref('currency_codes') }}
),

-- Step 2: Add surrogate key
keyed AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['currency_code']) }}  AS currency_key,
        currency_code,
        currency_name,
        region
    FROM src_seed
),

-- Step 3: Default record for orphan facts
default_record AS (
    SELECT
        '-1'                   AS currency_key,
        'UNK'                  AS currency_code,
        'Unknown Currency'     AS currency_name,
        'Unknown'              AS region
),

-- Step 4: Union with default record
final AS (
    SELECT * FROM keyed
    UNION ALL
    SELECT * FROM default_record
)

SELECT * FROM final
