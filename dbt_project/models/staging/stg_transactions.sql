-- =============================================================================
-- Staging: Transactions
-- =============================================================================
-- Source: RAW.TRANSACTIONS.CREDIT_CARD_TRANSACTIONS
-- Grain:  One row per credit card transaction
-- Pattern: src_data → renamed → cleaned → final
--
-- Transformations applied:
--   - Rename columns to project conventions
--   - Cast AMT to DECIMAL(10,2)
--   - Extract transaction_date from timestamp
--   - Strip 'fraud_' prefix from merchant names
--   - UPPER(state) for consistency
--   - TRIM whitespace on string fields
--   - Passthrough _loaded_at as _source_loaded_at
-- =============================================================================

WITH

-- Step 1: Pull raw data from source (no changes)
src_data AS (
    SELECT *
    FROM {{ source('raw_transactions', 'credit_card_transactions') }}
),

-- Step 2: Rename columns to project naming conventions
renamed AS (
    SELECT
        trans_num,
        trans_date_trans_time       AS transaction_at,
        cc_num                     AS card_number,
        amt                        AS transaction_amount,
        merchant                   AS merchant_name,
        category,
        first                      AS first_name,
        last                       AS last_name,
        gender,
        street,
        city,
        state,
        zip                        AS zip_code,
        lat                        AS latitude,
        long                       AS longitude,
        city_pop,
        job,
        dob                        AS date_of_birth,
        merch_lat                  AS merchant_latitude,
        merch_long                 AS merchant_longitude,
        is_fraud,
        unix_time,
        _loaded_at                 AS _source_loaded_at
    FROM src_data
),

-- Step 3: Clean — cast types, trim, standardize (non-destructive only)
cleaned AS (
    SELECT
        trans_num,
        transaction_at,
        transaction_at::DATE                           AS transaction_date,
        transaction_amount::DECIMAL(10,2)              AS transaction_amount,
        card_number,

        -- Strip 'fraud_' prefix from merchant names (artifact of Kaggle dataset)
        CASE
            WHEN merchant_name ILIKE 'fraud_%'
            THEN TRIM(SUBSTR(merchant_name, 7))
            ELSE TRIM(merchant_name)
        END                                            AS merchant_name,

        LOWER(TRIM(category))                          AS category,
        TRIM(first_name)                               AS first_name,
        TRIM(last_name)                                AS last_name,
        UPPER(TRIM(gender))                            AS gender,
        TRIM(street)                                   AS street,
        TRIM(city)                                     AS city,
        UPPER(TRIM(state))                             AS state,
        TRIM(zip_code)                                 AS zip_code,
        latitude,
        longitude,
        city_pop,
        TRIM(job)                                      AS job,
        date_of_birth,
        merchant_latitude,
        merchant_longitude,
        is_fraud,
        _source_loaded_at
    FROM renamed
),

-- Step 4: Final output — this is what downstream models see via ref()
final AS (
    SELECT * FROM cleaned
)

SELECT * FROM final
