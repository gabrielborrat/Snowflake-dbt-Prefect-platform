-- =============================================================================
-- Dimension: Merchants
-- =============================================================================
-- Grain: One row per unique merchant
-- Source: stg_transactions — deduplicated by merchant_name
-- Domain: Banking Transactions
--
-- A merchant can appear in multiple categories if the dataset has inconsistencies;
-- we pick the most frequent category for that merchant.
-- Includes a default record (key = '-1') for orphan fact handling.
-- =============================================================================

WITH

-- Step 1: Get all merchant records with their categories
src_data AS (
    SELECT
        merchant_name,
        category,
        merchant_latitude,
        merchant_longitude,
        COUNT(*) AS category_count
    FROM {{ ref('stg_transactions') }}
    GROUP BY
        merchant_name,
        category,
        merchant_latitude,
        merchant_longitude
),

-- Step 2: Deduplicate — keep the most frequent category per merchant
deduped AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY merchant_name
            ORDER BY category_count DESC
        ) AS _row_num
    FROM src_data
),

-- Step 3: Build dimension attributes
merchants AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['merchant_name']) }}  AS merchant_key,
        merchant_name,
        category,
        merchant_latitude,
        merchant_longitude
    FROM deduped
    WHERE _row_num = 1
),

-- Step 4: Default record for orphan facts
default_record AS (
    SELECT
        '-1'                    AS merchant_key,
        'Unknown Merchant'      AS merchant_name,
        'unknown'               AS category,
        CAST(NULL AS FLOAT)     AS merchant_latitude,
        CAST(NULL AS FLOAT)     AS merchant_longitude
),

-- Step 5: Final output
final AS (
    SELECT * FROM merchants
    UNION ALL
    SELECT * FROM default_record
)

SELECT * FROM final
