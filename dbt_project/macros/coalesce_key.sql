/*
  =============================================================================
  Macro: Coalesce Key (Orphan Fact Protection)
  =============================================================================
  Wraps the COALESCE pattern for dimension foreign keys in fact tables.
  If the dimension lookup returns NULL (no matching record), substitutes
  the default key '-1' so the fact joins to the "Unknown" default record.

  This is the Kimball pattern for handling orphan facts gracefully:
    - No fact rows are dropped from LEFT JOINs
    - Missing FKs join to a visible "Unknown" dimension record
    - Row counts are preserved
    - Data quality issues are surfaced (not hidden)

  Used in:
    - fact_transactions (4 FKs)
    - fact_daily_prices (3 FKs)
    - fact_exchange_rates (3 FKs)

  Usage:
    {{ coalesce_key('dim_table.surrogate_key') }}

  Output SQL:
    COALESCE(dim_table.surrogate_key, '-1')
  =============================================================================
*/

{% macro coalesce_key(key_column) %}
    COALESCE({{ key_column }}, '-1')
{% endmacro %}

