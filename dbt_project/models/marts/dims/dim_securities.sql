-- =============================================================================
-- Dimension: Securities
-- =============================================================================
-- Grain: One row per security (stock / ETF)
-- Source: stg_market_prices — deduplicated by ticker_symbol
-- Domain: Market Data
--
-- Security metadata (name, exchange, sector) is derived from the ticker symbol
-- using a CASE mapping. In production, this would come from a reference API
-- or seed file, but for this portfolio project, a static mapping is sufficient.
--
-- Includes a default record (key = '-1') for orphan fact handling.
-- =============================================================================

WITH

-- Step 1: Get distinct tickers from market data
src_data AS (
    SELECT DISTINCT
        ticker_symbol
    FROM {{ ref('stg_market_prices') }}
),

-- Step 2: Enrich with metadata (static mapping for portfolio project)
enriched AS (
    SELECT
        ticker_symbol,

        -- Security name mapping
        CASE ticker_symbol
            WHEN 'AAPL'    THEN 'Apple Inc.'
            WHEN 'MSFT'    THEN 'Microsoft Corporation'
            WHEN 'JPM'     THEN 'JPMorgan Chase & Co.'
            WHEN 'GS'      THEN 'Goldman Sachs Group Inc.'
            WHEN 'HSBA.L'  THEN 'HSBC Holdings plc'
            WHEN 'BNP.PA'  THEN 'BNP Paribas SA'
            WHEN 'SAP.DE'  THEN 'SAP SE'
            WHEN 'NOVN.SW' THEN 'Novartis AG'
            ELSE ticker_symbol
        END AS security_name,

        -- Exchange mapping (derived from ticker suffix)
        CASE
            WHEN ticker_symbol LIKE '%.L'  THEN 'LSE'         -- London Stock Exchange
            WHEN ticker_symbol LIKE '%.PA' THEN 'Euronext Paris'
            WHEN ticker_symbol LIKE '%.DE' THEN 'XETRA'       -- Frankfurt
            WHEN ticker_symbol LIKE '%.SW' THEN 'SIX'         -- Swiss Exchange
            ELSE 'NYSE/NASDAQ'                                  -- US tickers (no suffix)
        END AS exchange,

        -- Sector mapping
        CASE ticker_symbol
            WHEN 'AAPL'    THEN 'Technology'
            WHEN 'MSFT'    THEN 'Technology'
            WHEN 'JPM'     THEN 'Financial Services'
            WHEN 'GS'      THEN 'Financial Services'
            WHEN 'HSBA.L'  THEN 'Financial Services'
            WHEN 'BNP.PA'  THEN 'Financial Services'
            WHEN 'SAP.DE'  THEN 'Technology'
            WHEN 'NOVN.SW' THEN 'Healthcare'
            ELSE 'Other'
        END AS sector,

        -- Trading currency mapping
        CASE
            WHEN ticker_symbol LIKE '%.L'  THEN 'GBP'
            WHEN ticker_symbol LIKE '%.PA' THEN 'EUR'
            WHEN ticker_symbol LIKE '%.DE' THEN 'EUR'
            WHEN ticker_symbol LIKE '%.SW' THEN 'CHF'
            ELSE 'USD'
        END AS trading_currency

    FROM src_data
),

-- Step 3: Add surrogate key
keyed AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['ticker_symbol']) }}  AS security_key,
        ticker_symbol,
        security_name,
        exchange,
        sector,
        trading_currency
    FROM enriched
),

-- Step 4: Default record for orphan facts
default_record AS (
    SELECT
        '-1'                    AS security_key,
        'UNK'                   AS ticker_symbol,
        'Unknown Security'      AS security_name,
        'Unknown'               AS exchange,
        'Unknown'               AS sector,
        'UNK'                   AS trading_currency
),

-- Step 5: Final output
final AS (
    SELECT * FROM keyed
    UNION ALL
    SELECT * FROM default_record
)

SELECT * FROM final
