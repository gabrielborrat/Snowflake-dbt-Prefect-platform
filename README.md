# Snowflake · dbt · Prefect — Modern Data Stack Platform

> **End-to-end data platform** built with production-grade architecture patterns: Medallion layering, Kimball dimensional modeling, incremental processing, SCD2 history tracking, and full test/documentation coverage.

![Status](https://img.shields.io/badge/Status-In%20Progress-yellow)
![dbt](https://img.shields.io/badge/dbt%20Core-1.11-orange)
![Snowflake](https://img.shields.io/badge/Snowflake-Azure%20West%20Europe-56B4E9)
![Tests](https://img.shields.io/badge/Tests-85%20passing-brightgreen)
![Docs](https://img.shields.io/badge/Column%20Coverage-100%25-brightgreen)

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                                    │
│                                                                        │
│   Kaggle CSV (1.85M txns)    Yahoo Finance API    ECB / frankfurter    │
│   Credit Card Fraud Dataset   8 tickers (OHLCV)   6 FX pairs (EUR→X)  │
└──────────┬──────────────────────┬──────────────────────┬───────────────┘
           │                      │                      │
           ▼                      ▼                      ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    PYTHON INGESTION LAYER                               │
│                                                                        │
│   Incremental loading · Idempotency (MERGE / DELETE+INSERT)            │
│   Snowflake Connector · Loguru logging · Error handling                │
└──────────┬──────────────────────┬──────────────────────┬───────────────┘
           │                      │                      │
           ▼                      ▼                      ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 SNOWFLAKE — RAW (Bronze Layer)                          │
│                                                                        │
│   RAW.TRANSACTIONS    RAW.MARKET_DATA    RAW.EXCHANGE_RATES            │
│   RBAC · Warehouse separation · Cost monitoring                        │
└──────────┬──────────────────────┬──────────────────────┬───────────────┘
           │                      │                      │
           ▼                      ▼                      ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 dbt — STAGING (Silver Layer)                            │
│                                                                        │
│   stg_transactions    stg_market_prices    stg_exchange_rates          │
│   Views · CTE pattern (src → renamed → cleaned → final)               │
│   1:1 with source · Type casting · Column standardization              │
└──────────┬──────────────────────┬──────────────────────┬───────────────┘
           │                      │                      │
           ▼                      ▼                      ▼
┌────────────────────────────────────────────────────────────────────────┐
│              dbt — MARTS (Gold Layer · Kimball Star Schema)            │
│                                                                        │
│   DIMENSIONS                        FACTS (incremental, merge)         │
│   ┌─────────────┐                   ┌──────────────────────┐           │
│   │ dim_dates    │ (date spine)      │ fact_transactions    │ 1.85M    │
│   │ dim_currencies│ (seed-based)     │ fact_daily_prices    │ 12K      │
│   │ dim_customers│ (+ SCD2 snap)    │ fact_exchange_rates  │ 9.4K     │
│   │ dim_merchants│                   └──────────────────────┘           │
│   │ dim_securities│                                                     │
│   └─────────────┘                   Conformed dims enable              │
│   Default records (key='-1')        cross-domain analysis              │
│   Surrogate keys (MD5 hash)                                            │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Key Technical Highlights

| Area | What's Implemented |
|------|--------------------|
| **Dimensional Modeling** | Kimball star schema with 5 dimensions, 3 fact tables, conformed dimensions (`dim_dates`, `dim_currencies`) enabling cross-domain analysis |
| **Incremental Processing** | Fact tables use `merge` strategy with `is_incremental()` filter — only new/changed rows are processed on each run |
| **SCD Type 2** | `snap_customers` tracks customer attribute changes over time (city, state, job) using dbt's `check` strategy |
| **Orphan Fact Handling** | Default dimension records (`key = '-1'`) + `{{ coalesce_key() }}` macro — no fact rows dropped from LEFT JOINs |
| **Custom Macros (DRY)** | `safe_divide`, `coalesce_key`, `cents_to_dollars` — reusable patterns across all models |
| **Testing Pyramid** | 85 tests: schema tests (not_null, unique), referential integrity (relationships), domain validation (accepted_values), 4 singular business-rule tests |
| **Documentation as Code** | 143/143 columns documented (100%), `persist_docs` pushes descriptions to Snowflake column COMMENTs |
| **Ingestion** | Python scripts with incremental loading, idempotency (MERGE for APIs, DELETE+INSERT for CSV), Loguru logging |
| **Snowflake Governance** | RBAC (3 roles), warehouse separation (ingest vs transform vs analytics), cost monitoring queries |

---

## Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Storage & Compute** | Snowflake (Azure West Europe) | Cloud data warehouse — RBAC, virtual warehouses, zero-copy cloning |
| **Transformation** | dbt Core 1.11 | SQL-based transformations, testing, documentation, incremental models |
| **Ingestion** | Python (snowflake-connector, yfinance, requests) | API + CSV ingestion with incremental loading and idempotency |
| **Orchestration** | Prefect OSS | Workflow orchestration — ingestion, dbt runs, tests, notifications |
| **BI / Consumption** | Power BI | Dashboards and reports on top of the Gold layer |
| **Version Control** | Git / GitHub | Source control, CI, project showcase |

---

## Data Domains

This platform integrates **two financial data domains** through conformed dimensions:

### 1. Financial Transactions (Banking)
- **Source:** Kaggle Credit Card Fraud Detection dataset (1.85M transactions)
- **Grain:** One row per credit card transaction
- **Analysis:** Fraud detection, spending patterns, customer segmentation

### 2. Stock Market & Portfolio Analytics
- **Source:** Yahoo Finance API (8 tickers — US tech, US banks, EU banks, EU blue chips)
- **Grain:** One row per security per trading day
- **Analysis:** Price trends, daily returns, volatility, sector comparison

### Cross-Domain Bridge
- **Exchange Rates** (ECB via frankfurter.app) — enables currency-normalized cross-domain analysis
- **Conformed Dimensions** (`dim_dates`, `dim_currencies`) — shared across all three fact tables

---

## Repository Structure

```
├── snowflake/                  # Snowflake infrastructure (DDL)
│   ├── setup/                  #   Databases, warehouses, RBAC, file formats
│   └── maintenance/            #   Cost monitoring queries
│
├── ingestion/                  # Python ingestion layer
│   ├── sources/                #   Per-source scripts (transactions, prices, rates)
│   ├── utils/                  #   Snowflake connector, logging
│   └── config.py               #   Environment configuration
│
├── dbt_project/                # dbt transformation layer
│   ├── models/
│   │   ├── staging/            #   Silver layer (views, 1:1 with source)
│   │   └── marts/
│   │       ├── dims/           #   Gold layer — Kimball dimensions
│   │       └── facts/          #   Gold layer — Kimball facts (incremental)
│   ├── snapshots/              #   SCD Type 2 (snap_customers)
│   ├── seeds/                  #   Reference data (currency_codes)
│   ├── macros/                 #   Custom macros (safe_divide, coalesce_key, ...)
│   └── tests/                  #   Singular tests (business rule validation)
│
├── orchestration/              # Prefect flows (coming soon)
├── dashboards/                 # Power BI reports (coming soon)
├── docs/                       # Architecture docs & implementation plan
└── architecture/diagrams/      # Architecture diagrams
```

---

## Project Progress

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 0** | Project Scaffolding | ✅ Complete |
| **Phase 1** | Snowflake Infrastructure (databases, warehouses, RBAC) | ✅ Complete |
| **Phase 2** | Python Ingestion Layer (APIs + CSV) | ✅ Complete |
| **Phase 3** | dbt Transformation Layer (staging → dims → facts → snapshots → tests → docs) | ✅ Complete |
| **Phase 4** | Prefect Orchestration (flows, schedules, error handling) | 🔜 Next |
| **Phase 5** | Power BI Dashboards | 📋 Planned |
| **Phase 6** | Final Documentation & Portfolio Polish | 📋 Planned |

---

## Quick Start

```bash
# 1. Clone and set up environment
git clone https://github.com/gabrielborrat/Snowflake-dbt-Prefect-platform.git
cd Snowflake-dbt-Prefect-platform
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configure credentials
cp .env.example .env
# Edit .env with your Snowflake credentials

# 3. Set up Snowflake infrastructure
# Run scripts in snowflake/setup/ (01 → 04) in Snowflake worksheet

# 4. Run ingestion
python -m ingestion.sources.ingest_exchange_rates
python -m ingestion.sources.ingest_market_prices
python -m ingestion.sources.ingest_transactions

# 5. Run dbt
cd dbt_project
set -a && source ../.env && set +a
dbt deps
dbt seed
dbt snapshot
dbt run
dbt test                    # 85 tests
dbt docs generate           # Documentation site
dbt docs serve              # View DAG at localhost:8080
```

---

## Testing

```
85 tests — 81 generic (YAML-declared) + 4 singular (custom SQL)

Test pyramid:
  ✅ Schema tests        — not_null, unique on all keys
  ✅ Referential integrity — relationships across star schema (10 FK tests)
  ✅ Domain validation    — accepted_values for enums and flags
  ✅ Business rules       — no future dates, positive prices, row count reconciliation
  ✅ Source freshness     — 3/3 sources passing
```

---

## License

This project is for **portfolio and educational purposes**.

Data sources:
- [Kaggle Credit Card Fraud Detection](https://www.kaggle.com/datasets/kartik2112/fraud-detection) — Open dataset
- [Yahoo Finance](https://finance.yahoo.com/) via `yfinance` — Market data API
- [frankfurter.app](https://www.frankfurter.app/) — ECB exchange rates (public API)

