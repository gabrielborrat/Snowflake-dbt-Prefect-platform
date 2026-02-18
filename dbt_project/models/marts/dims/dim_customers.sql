-- =============================================================================
-- Dimension: Customers
-- =============================================================================
-- Grain: One row per unique customer (current state)
-- Source: stg_transactions — deduplicated by card_number
-- Domain: Banking Transactions
--
-- Customer identity is based on card_number (unique per card holder in dataset).
-- SCD2 historical tracking via snap_customers (Sub-Phase 3.5).
-- Includes a default record (key = '-1') for orphan fact handling.
-- =============================================================================

WITH

-- Step 1: Get all customer records from transactions
src_data AS (
    SELECT
        card_number,
        first_name,
        last_name,
        gender,
        street,
        city,
        state,
        zip_code,
        latitude,
        longitude,
        city_pop,
        job,
        date_of_birth,
        _source_loaded_at
    FROM {{ ref('stg_transactions') }}
),

-- Step 2: Deduplicate — keep the most recent record per card_number
deduped AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY card_number
            ORDER BY _source_loaded_at DESC
        ) AS _row_num
    FROM src_data
),

-- Step 3: Build dimension attributes
customers AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['card_number']) }}  AS customer_key,
        card_number,
        first_name,
        last_name,
        first_name || ' ' || last_name                          AS full_name,
        gender,
        street,
        city,
        state,
        zip_code,
        latitude,
        longitude,
        city_pop,
        job,
        date_of_birth,

        -- Derived: age group bucket (based on date of birth)
        CASE
            WHEN date_of_birth IS NULL THEN 'Unknown'
            WHEN DATEDIFF(year, date_of_birth, CURRENT_DATE()) < 25 THEN '18-24'
            WHEN DATEDIFF(year, date_of_birth, CURRENT_DATE()) < 35 THEN '25-34'
            WHEN DATEDIFF(year, date_of_birth, CURRENT_DATE()) < 45 THEN '35-44'
            WHEN DATEDIFF(year, date_of_birth, CURRENT_DATE()) < 55 THEN '45-54'
            WHEN DATEDIFF(year, date_of_birth, CURRENT_DATE()) < 65 THEN '55-64'
            ELSE '65+'
        END                                                      AS age_group

    FROM deduped
    WHERE _row_num = 1
),

-- Step 4: Default record for orphan facts
default_record AS (
    SELECT
        '-1'                    AS customer_key,
        CAST(NULL AS NUMBER)    AS card_number,
        'Unknown'               AS first_name,
        'Customer'              AS last_name,
        'Unknown Customer'      AS full_name,
        'U'                     AS gender,
        NULL                    AS street,
        NULL                    AS city,
        NULL                    AS state,
        NULL                    AS zip_code,
        CAST(NULL AS FLOAT)     AS latitude,
        CAST(NULL AS FLOAT)     AS longitude,
        CAST(NULL AS NUMBER)    AS city_pop,
        NULL                    AS job,
        CAST(NULL AS DATE)      AS date_of_birth,
        'Unknown'               AS age_group
),

-- Step 5: Final output
final AS (
    SELECT * FROM customers
    UNION ALL
    SELECT * FROM default_record
)

SELECT * FROM final
