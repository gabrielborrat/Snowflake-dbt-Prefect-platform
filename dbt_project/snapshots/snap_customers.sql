-- =============================================================================
-- Snapshot: Customers (SCD Type 2)
-- =============================================================================
-- Tracks changes to customer attributes over time.
-- Enables historical analysis: "What was the fraud rate for customers
-- in New York last year?" even if those customers have since moved.
--
-- Strategy: check (no reliable updated_at in source data)
-- Tracked columns: city, state, zip_code, job (relocations + career changes)
-- Unique key: card_number (natural key for customer identity)
--
-- Execution order: dbt snapshot runs BEFORE dbt run
-- Target: ANALYTICS.SNAPSHOTS.snap_customers
--
-- SCD2 columns auto-managed by dbt:
--   dbt_valid_from  — when this version became active
--   dbt_valid_to    — when superseded (NULL = current record)
--   dbt_scd_id      — unique row identifier
--   dbt_updated_at  — insertion timestamp
-- =============================================================================

{% snapshot snap_customers %}

{{
    config(
        target_schema='snapshots',
        unique_key='card_number',
        strategy='check',
        check_cols=['city', 'state', 'zip_code', 'job'],
        invalidate_hard_deletes=True
    )
}}

-- Deduplicated customer records from staging
-- We snapshot the staging-level data (close to source) to capture
-- the raw state before any mart-level transformations
WITH

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

deduped AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY card_number
            ORDER BY _source_loaded_at DESC
        ) AS _row_num
    FROM src_data
)

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
FROM deduped
WHERE _row_num = 1

{% endsnapshot %}
