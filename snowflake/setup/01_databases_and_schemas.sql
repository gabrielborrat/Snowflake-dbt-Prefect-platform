-- =============================================================================
-- 01 — Databases & Schemas
-- =============================================================================
-- Run as: SYSADMIN (or ACCOUNTADMIN)
-- Purpose: Create the database and schema structure for the MDS platform.
--
-- Layout:
--   RAW         → Bronze layer (ingested source data)
--     ├── TRANSACTIONS    → Credit card transaction data (Kaggle CSV)
--     ├── MARKET_DATA     → Stock prices (yfinance API)
--     └── EXCHANGE_RATES  → FX rates (frankfurter.app API)
--
--   ANALYTICS   → Silver + Gold layers (dbt transformations)
--     ├── STAGING         → dbt staging models (cleaned, standardized)
--     └── MARTS           → dbt dimensional models (facts + dims)
-- =============================================================================

USE ROLE SYSADMIN;

-- -----------------------------------------------------------------------------
-- RAW Database (Bronze Layer)
-- -----------------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS RAW
    COMMENT = 'Bronze layer — raw ingested data from all sources';

-- Schema: Credit card transactions (Kaggle CSV)
CREATE SCHEMA IF NOT EXISTS RAW.TRANSACTIONS
    COMMENT = 'Raw credit card transaction data from Kaggle';

-- Schema: Stock market prices (yfinance API)
CREATE SCHEMA IF NOT EXISTS RAW.MARKET_DATA
    COMMENT = 'Raw daily stock prices from Yahoo Finance API';

-- Schema: Exchange rates (frankfurter.app / ECB API)
CREATE SCHEMA IF NOT EXISTS RAW.EXCHANGE_RATES
    COMMENT = 'Raw daily exchange rates from ECB via frankfurter.app';

-- -----------------------------------------------------------------------------
-- ANALYTICS Database (Silver + Gold Layers)
-- -----------------------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS ANALYTICS
    COMMENT = 'Silver + Gold layers — dbt transformations and dimensional models';

-- Schema: Staging (Silver Layer)
CREATE SCHEMA IF NOT EXISTS ANALYTICS.STAGING
    COMMENT = 'Silver layer — cleaned and standardized data (dbt staging models)';

-- Schema: Marts (Gold Layer)
CREATE SCHEMA IF NOT EXISTS ANALYTICS.MARTS
    COMMENT = 'Gold layer — dimensional models for BI consumption (dbt mart models)';

-- -----------------------------------------------------------------------------
-- Verification
-- -----------------------------------------------------------------------------
SHOW DATABASES;
SHOW SCHEMAS IN DATABASE RAW;
SHOW SCHEMAS IN DATABASE ANALYTICS;
