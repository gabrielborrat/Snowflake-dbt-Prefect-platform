# 📘 Snowflake Modern Data Stack Portfolio
## Project Memory – Architecture, Tools, and Design Decisions

---

## 1. Objective

Build a **credible, senior-grade Modern Data Stack (MDS) portfolio project** demonstrating:

- Snowflake data warehousing
- dbt-based transformations
- External orchestration
- Professional ingestion design
- BI consumption
- Governance mindset

Target positioning:
> Analytics Engineer / Modern Data Stack Engineer / Data Architect (Finance / Consulting / Banking)

---

## 2. Core Stack Philosophy

Snowflake follows a **separation of concerns** model:

| Layer | Responsibility | Tool |
|-------|---------------|------|
| Storage & Compute | Execution engine | Snowflake |
| Transformation | Modeling & testing | dbt Core |
| Orchestration | Control plane | Prefect |
| Ingestion | Data acquisition | Python scripts |
| Consumption | Analytics | Power BI |

Key principle:
> Snowflake executes. Orchestrators control. dbt structures transformations.

---

## 3. Cloud Model

- Snowflake does **not** have its own cloud
- Runs on AWS / Azure / GCP
- Infrastructure is fully abstracted
- User manages only logical resources

Recommended for European / Microsoft-centric context:
> Snowflake on Azure (West Europe)

Cloud choice is not a major portfolio differentiator.

---

## 4. Snowflake + dbt Relationship

### Snowflake
- Stores data
- Executes SQL
- Manages scaling, optimization, security

### dbt
- Compiles SQL
- Manages dependencies
- Runs tests
- Generates documentation

Execution flow:
```
dbt → compiles SQL → Snowflake executes → results stored in Snowflake
```

### dbt Versions

| Tool | Status |
|------|--------|
| dbt Core | Open source, free (recommended) |
| dbt Cloud | Paid, trial only |

Portfolio uses **dbt Core**.

---

## 5. Orchestration Layer

Orchestration is **external by design**.

Snowflake does not provide full orchestration.

### Industry Standards

| Level | Tool |
|-------|------|
| Analytics | dbt Cloud |
| Enterprise | Airflow |
| Modern | Prefect / Dagster |
| Lightweight | Snowflake Tasks |

### Portfolio Choice

> Prefect (open source, Python-native, lightweight)

Used to orchestrate:
- ingestion
- dbt runs
- tests
- notifications

---

## 6. Cost & Licensing Strategy

| Component | Cost |
|-----------|------|
| Snowflake | Free trial credits |
| dbt Core | Free |
| Prefect OSS | Free |
| Python | Free |
| Power BI | Free tier / Desktop |

No paid tooling required.

---

## 7. Ingestion Layer Design

Two options were evaluated:

### Airbyte
- Open source
- Connector-based
- Higher operational overhead
- Opaque logic

### Python (Selected)
- Full control
- Deterministic logic
- Easy debugging
- Clean GitHub story
- Lower complexity

Decision:
> Use Python ingestion scripts orchestrated by Prefect.

Capabilities demonstrated:
- API ingestion
- CSV ingestion
- Incremental loading
- Idempotency
- Logging
- Error handling

---

## 8. End-to-End Reference Architecture

```
Sources (API / CSV / Kaggle)
        ↓
Python Ingestion
        ↓
Snowflake RAW
        ↓
dbt STAGING
        ↓
dbt MARTS
        ↓
Snowflake ANALYTICS
        ↓
Power BI

Prefect orchestrates all steps
```

---

## 9. Data Modeling Strategy (dbt)

Standard analytics engineering structure:

```
models/
  staging/
  marts/
    facts/
    dims/
```

Schemas:

| Layer | Purpose |
|-------|---------|
| RAW | Ingested source data |
| STAGING | Cleaned, standardized |
| MARTS | Business models |

Key concepts:
- Surrogate keys
- Incremental models
- SCD2 snapshots
- Dimensional modeling (Kimball)
- Currency normalization
- Date spine

---

## 10. Governance & Quality

Lightweight but explicit governance:

### Implemented via dbt
- Source freshness
- Not-null tests
- Unique tests
- Referential integrity
- Documentation

### Snowflake
- Role-based access model
- Warehouse separation
- Cost monitoring
- Auto-suspend

Governance is treated as a design concern, not an afterthought.

---

## 11. BI & Consumption Layer

Mandatory for portfolio credibility.

Tool:
> Power BI

Artifacts:
- KPI dashboards
- Financial / transaction analytics
- Screenshots
- Metric definitions

Purpose:
> Demonstrate business value of the platform.

---

## 12. Repository Structure (Target)

```
snowflake-mds-portfolio/
│
├── README.md
├── architecture/
├── ingestion/
├── dbt/
├── snowflake/
├── dashboards/
└── docs/
```

Includes:
- SQL DDL
- Role definitions
- Prefect flows
- dbt models
- BI assets
- Documentation

---

## 13. Learning & Implementation Phases

### Phase 1 – Snowflake Fundamentals
- Warehouses
- Time Travel
- Cloning
- Cost model

### Phase 2 – SQL Analytics
- Window functions
- CTEs
- QUALIFY
- Incremental logic

### Phase 3 – dbt
- Models
- Tests
- Docs
- Snapshots

### Phase 4 – Orchestration
- Prefect flows
- Scheduling
- Retries
- Logging

### Phase 5 – Governance & Storytelling
- RBAC
- Cost discipline
- Documentation

---

## 14. Professional Positioning

After completion, legitimate positioning:

> Designed and implemented a Modern Data Stack platform using Snowflake, dbt, Python, and Prefect, including ingestion pipelines, dimensional modeling, data quality testing, orchestration, governance, and BI delivery.

---

## 15. Interview Narrative (Key Messages)

### Orchestration
> Snowflake executes workloads. Orchestration is external via Prefect or dbt Cloud in production.

### dbt
> dbt provides modular transformations, testing, documentation, and version control.

### Ingestion
> Python pipelines allow full control and reliability. Managed tools are used in enterprise environments.

### Cloud
> Snowflake abstracts infrastructure. Architecture is cloud-agnostic.

---

## 16. Final Stack (Portfolio Baseline)

```
Snowflake (trial)
dbt Core
Prefect OSS
Python ingestion
Power BI
GitHub
```

This stack is:
- Free
- Industry-aligned
- Reproducible
- Recruiter-friendly
- Consulting-grade

---

## 17. Guiding Principles

1. Architecture before tools
2. Reproducibility over demos
3. Governance from day one
4. Business framing
5. Cost awareness
6. Clear documentation

---

## 18. Snowflake is Pattern-Agnostic

Snowflake is a **compute and storage engine**. It does not impose any data architecture.
You can implement any pattern using its building blocks (databases, schemas, tables, views, roles, warehouses).

> Snowflake gives you the bricks. You decide the blueprint.

### Medallion Maps to Our Stack

| Medallion Layer | Our Equivalent | Implementation |
|-----------------|---------------|----------------|
| 🥉 Bronze | RAW | Python ingestion → Snowflake |
| 🥈 Silver | STAGING | dbt cleans & standardizes |
| 🥇 Gold | MARTS | dbt dimensional models → Power BI consumes |

### Architecture Decision

> **Medallion + Kimball** — Medallion governs the overall data flow (quality progression), Kimball governs the Gold/MARTS layer (dimensional modeling for BI).

Rationale:
- Medallion answers: *"How does data mature through the platform?"*
- Kimball answers: *"How is data structured for business consumption?"*
- Together they tell a complete story — from raw ingestion to executive dashboard
- Both are industry standards recognized by hiring managers

---

## 19. Industry Data Patterns – Full Landscape

### 19.1 Medallion Architecture (Bronze / Silver / Gold)

- **Origin**: Databricks / Lakehouse paradigm
- **Philosophy**: Data quality improves layer by layer
- **Best for**: General-purpose analytics platforms, data lakes
- **Seen at**: Companies using Databricks, Snowflake, cloud-native stacks
- **Strengths**: Simple to understand, clean separation, easy to debug
- **Weaknesses**: Can lead to duplication if not managed well

### 19.2 Kimball Dimensional Modeling (Star / Snowflake Schema)

- **Origin**: Ralph Kimball, 1990s — still the gold standard for BI
- **Philosophy**: Model data around business processes (facts) and descriptive context (dimensions)
- **Best for**: BI, dashboards, reporting, Power BI / Tableau consumption
- **Seen at**: Banking, retail, consulting, insurance — everywhere BI matters
- **Strengths**: Fast queries, intuitive for analysts, industry standard
- **Weaknesses**: Requires upfront design effort, less flexible for ad-hoc exploration
- **Key concepts**: Fact tables, dimension tables, surrogate keys, conformed dimensions, SCDs, grain

### 19.3 Data Vault 2.0

- **Origin**: Dan Linstedt — designed for enterprise-scale, audit-heavy environments
- **Structure**: Hub (business keys) ↔ Link (relationships) ↔ Satellite (attributes + history)
- **Best for**: Banks, insurance, government — regulated, audit-heavy environments
- **Seen at**: Large European banks, government agencies, telecoms
- **Strengths**: Full historization, parallel loading, source-system agnostic, audit-ready
- **Weaknesses**: Complex, verbose, steep learning curve, requires a BI layer on top (often Kimball)
- **Key concepts**: Hubs, Links, Satellites, hash keys, load timestamps, record source tracking

> In practice, many enterprises use Data Vault as the Silver layer and Kimball as the Gold layer.

### 19.4 One Big Table (OBT)

- **Origin**: Modern analytics trend, especially with columnar engines
- **Philosophy**: Eliminate joins — one massively wide, denormalized table
- **Best for**: Small-to-mid datasets, fast prototyping, simple BI
- **Seen at**: Startups, product analytics teams, embedded analytics
- **Strengths**: Dead simple to query, fast for BI tools, no join confusion
- **Weaknesses**: Data duplication, hard to maintain, doesn't scale with complexity

### 19.5 Inmon (Enterprise Data Warehouse / 3NF)

- **Origin**: Bill Inmon, 1990s — the "father of data warehousing"
- **Flow**: Source → Normalized (3NF) Enterprise DWH → Departmental Data Marts
- **Best for**: Large enterprises with centralized data teams
- **Seen at**: Legacy banking, insurance, large corporates
- **Strengths**: No redundancy, strong consistency, enterprise-wide truth
- **Weaknesses**: Slow to build, complex ETL, hard to iterate, rigid

> Inmon vs Kimball is one of the oldest debates in data engineering. Modern stacks lean Kimball because of dbt and agile delivery.

### 19.6 Activity Schema

- **Origin**: Ahmed Elsamadisi (Narrator.ai) — recent pattern
- **Structure**: activity_stream (entity_id, activity, timestamp, features)
- **Best for**: Event-driven businesses (SaaS, e-commerce, product analytics)
- **Seen at**: Startups, SaaS companies, product-led growth teams
- **Strengths**: Extremely flexible, no upfront modeling needed
- **Weaknesses**: Niche, not widely adopted, can be hard to query for complex analytics

### 19.7 Lambda Architecture

- **Origin**: Nathan Marz (creator of Apache Storm)
- **Flow**: Source → Batch Layer (complete, slow) + Speed Layer (real-time, fast) → Serving Layer
- **Best for**: Systems needing both historical accuracy and real-time data
- **Seen at**: AdTech, IoT, fraud detection, trading platforms
- **Strengths**: Handles both batch and streaming use cases
- **Weaknesses**: Dual codebase maintenance, complex operations, code duplication

### 19.8 Kappa Architecture

- **Origin**: Jay Kreps (co-creator of Kafka) — simplification of Lambda
- **Philosophy**: Everything is a stream — no separate batch layer
- **Best for**: Event-driven systems, real-time-first platforms
- **Seen at**: Kafka-centric platforms, fintech, ride-sharing
- **Strengths**: Single codebase, simpler than Lambda
- **Weaknesses**: Not all workloads are naturally streaming, reprocessing can be expensive

### 19.9 Data Mesh

- **Origin**: Zhamak Dehghani (Thoughtworks), 2019
- **Philosophy**: Decentralize data ownership to domain teams, treat data as a product
- **Best for**: Large orgs with many domains (100+ engineers)
- **Seen at**: Zalando, Netflix, Saxo Bank, large enterprises
- **Strengths**: Scales organization, removes bottlenecks, domain expertise
- **Weaknesses**: Requires mature engineering culture, hard to implement, governance is tricky
- **Four principles**: Domain ownership, Data as a product, Self-serve platform, Federated governance

### 19.10 Data Fabric

- **Origin**: Gartner — vendor-driven concept
- **Philosophy**: Unified metadata and AI-driven integration across all data sources
- **Best for**: Enterprises with sprawling, heterogeneous data landscapes
- **Seen at**: Large enterprises using IBM, Informatica, Talend
- **Strengths**: Automation, metadata-driven, cross-platform
- **Weaknesses**: Mostly vendor hype, expensive, hard to implement from scratch

### Complexity Summary

| Pattern | When You'd Use It | Complexity |
|---------|-------------------|------------|
| Medallion | General-purpose data platform | ⭐⭐ |
| Kimball | BI & analytics consumption | ⭐⭐⭐ |
| Data Vault | Audit-heavy, regulated industries | ⭐⭐⭐⭐ |
| OBT | Quick analytics, small datasets | ⭐ |
| Inmon (3NF) | Legacy enterprise DWH | ⭐⭐⭐⭐ |
| Activity Schema | Event-driven SaaS | ⭐⭐ |
| Lambda | Batch + real-time hybrid | ⭐⭐⭐⭐⭐ |
| Kappa | Streaming-first | ⭐⭐⭐⭐ |
| Data Mesh | Organizational decentralization | ⭐⭐⭐⭐⭐ |
| Data Fabric | Enterprise metadata integration | ⭐⭐⭐⭐⭐ |

---

## 20. Data Pattern ↔ Tool Stack Alignment

The data pattern chosen shapes the tools needed. The tools available often push toward certain patterns. They are deeply coupled.

### Medallion + Kimball → Modern Data Stack (MDS)

```
Ingestion:      Python / Fivetran / Airbyte
Storage:        Snowflake / BigQuery / Redshift
Transformation: dbt
Orchestration:  Prefect / Airflow / Dagster
Consumption:    Power BI / Tableau / Looker
```

Why: Column-store warehouses are optimized for star schema queries. dbt was designed for staging → marts. ELT approach — load raw, transform in-warehouse. BI tools expect dimensional models.

> dbt + Snowflake is the natural home for Medallion + Kimball.

### Data Vault 2.0 → Enterprise Audit-Heavy Stack

```
Ingestion:      Informatica / Talend / custom ETL
Storage:        Snowflake / SQL Server / Teradata
Transformation: dbt (with automate-dv package) / stored procedures
Orchestration:  Airflow / Control-M / enterprise schedulers
Consumption:    Kimball marts on top → Power BI / Tableau
```

Why: Needs hash key generation, load timestamps, record source tracking. Still requires a Kimball layer on top for BI.

### Lambda → Batch + Real-Time Hybrid Stack

```
Batch layer:    Spark / Snowflake / BigQuery
Speed layer:    Kafka + Flink / Spark Streaming / ksqlDB
Serving:        Druid / ClickHouse / Elasticsearch / Redis
Orchestration:  Airflow / Kubernetes jobs
Ingestion:      Kafka / Debezium (CDC)
```

Why: Two separate engines needed — batch + streaming. Snowflake + dbt don't play here.

### Kappa → Streaming-First Stack

```
Streaming:      Kafka + Flink / Kafka Streams / ksqlDB
Storage:        Kafka (as source of truth) / S3 / Delta Lake
Serving:        ClickHouse / Druid / Pinot / Materialize
Orchestration:  Kubernetes / Flink job management
```

Why: Everything is an event stream. No traditional batch warehouse. No place for Snowflake, dbt, or Power BI.

### Data Mesh → Decentralized Platform Stack

```
Platform:       Snowflake (multi-database) / Databricks Unity Catalog / BigQuery
Transformation: dbt (per domain team)
Data Catalog:   DataHub / Atlan / Alation / OpenMetadata
Governance:     Collibra / Snowflake governance features
Orchestration:  Airflow / Prefect (per domain)
Contracts:      Data contracts (protobuf / JSON Schema / soda)
```

Why: Same core tools as MDS, plus governance, catalog, and contract tooling.

### Lakehouse → Databricks-Centric Stack

```
Storage:        Delta Lake / Iceberg / Hudi (on S3/ADLS)
Compute:        Spark (Databricks)
Transformation: Spark SQL / dbt-spark / notebooks
ML:             MLflow / Databricks ML
Orchestration:  Databricks Workflows / Airflow
Consumption:    Databricks SQL / Power BI / Tableau
```

Why: Open file formats replace the proprietary warehouse. Single engine for data engineering + data science.

### Pattern × Stack Compatibility Matrix

| Pattern | Snowflake | dbt | Streaming | Prefect | Power BI | Governance |
|---------|-----------|-----|-----------|---------|----------|------------|
| Medallion + Kimball | ✅ | ✅ | ❌ | ✅ | ✅ | dbt tests |
| Data Vault | ✅ | ✅ (+ vault pkg) | ❌ | ⚠️ | ✅ | Heavy |
| Lambda | ⚠️ (batch only) | ❌ | Kafka + Flink | ❌ | ⚠️ | Complex |
| Kappa | ❌ | ❌ | Kafka | ❌ | ❌ | Complex |
| Data Mesh | ✅ | ✅ | Optional | ✅ | ✅ | Catalog + Contracts |
| Lakehouse | ⚠️ | ⚠️ | Optional | ⚠️ | ✅ | Unity Catalog |
| OBT | ✅ | ✅ | ❌ | ✅ | ✅ | Minimal |

### Our Stack Fit Summary

| ✅ Perfect fit | ⚠️ Possible with effort | ❌ Wrong tool |
|---------------|--------------------------|--------------|
| Medallion + Kimball | Data Vault (via dbt packages) | Lambda |
| OBT | Data Mesh (needs catalog layer) | Kappa |
| | | Pure Lakehouse |

> The MDS stack is the analytics engineering stack. It dominates in finance & banking analytics, consulting BI delivery, corporate data platforms — any use case where batch processing + BI consumption is the goal.

### Interview-Ready Statement

> *"I chose Snowflake, dbt, and Prefect because my architecture follows a Medallion + Kimball pattern — the industry standard for analytics engineering. If the use case required real-time streaming, I'd reach for Kafka and Flink. If it needed ML at scale, I'd consider a Lakehouse on Databricks. The stack should serve the pattern, not the other way around."*

---

## 21. Data Domain Decision

### Domain Choice: Financial Transactions + Market Data (Combined)

Two business domains combined into a single platform for maximum portfolio impact:

| Domain | Business Context | Source Type |
|--------|-----------------|-------------|
| 🏦 Banking Transactions | Retail banking / payments analytics | CSV (Kaggle) |
| 📈 Market / Investment Data | Stock market & portfolio monitoring | API (Yahoo Finance / Alpha Vantage) |
| 💱 Exchange Rates | Currency conversion & exposure | API (ECB / ExchangeRate-API) |

### Why Combined?

- Two fact domains show ability to model multiple business processes
- Cross-domain analysis via conformed dimensions — a senior Kimball skill
- Richer ingestion story: CSV + multiple APIs
- Stronger Power BI dashboards with cross-domain correlation

---

## 22. Cross-Domain Analysis – Conformed Dimensions Design

### Core Principle

In Kimball, you **never join fact to fact directly**. Cross-domain analysis is enabled through **conformed dimensions** — dimensions shared identically across multiple fact tables.

### Conformed Dimensions (shared across domains)

| Dimension | Used by Transactions | Used by Market Data | Used by Exchange Rates |
|-----------|:---:|:---:|:---:|
| `dim_dates` | ✅ | ✅ | ✅ |
| `dim_currencies` | ✅ | ✅ | ✅ |

### Domain-Specific Dimensions

| Dimension | Domain | Purpose |
|-----------|--------|---------|
| `dim_customers` | Transactions | Customer segmentation, SCD2 |
| `dim_merchants` | Transactions | Merchant category, location |
| `dim_securities` | Market Data | Stock ticker, sector, exchange |
| `dim_exchanges` | Market Data | Exchange metadata, timezone |

---

## 23. Gold Layer Dimensional Model

### Fact Tables

| Fact Table | Grain | Source | Incremental? |
|-----------|-------|--------|:---:|
| `fact_transactions` | One row per transaction | Kaggle CSV | ✅ |
| `fact_daily_prices` | One row per security per day | Yahoo Finance / Alpha Vantage API | ✅ |
| `fact_exchange_rates` | One row per currency pair per day | ExchangeRate API / ECB | ✅ |

### Full Star Schema Layout

```
                          ┌─────────────────┐
                          │    dim_dates     │ ← CONFORMED
                          │  (date spine)    │
                          └────────┬─────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
              ┌─────┴──────┐ ┌────┴────────┐ ┌───┴──────────────┐
              │   fact_     │ │   fact_     │ │   fact_          │
              │transactions │ │daily_prices │ │exchange_rates    │
              └─────┬──────┘ └────┬────────┘ └───┬──────────────┘
                    │              │              │
                    ├──────────────┼──────────────┤
                    │              │              │
              ┌─────┴──────┐      │       ┌──────┴──────┐
              │dim_customers│      │       │dim_currencies│ ← CONFORMED
              │  (SCD2)     │      │       └─────────────┘
              └────────────┘      │
                           ┌──────┴──────┐
                           │dim_securities│
                           └─────────────┘
```

### `fact_exchange_rates` as a Separate Fact

This fact table is the **bridge** enabling cross-domain currency analysis:
- Convert transaction amounts to a base currency using the rate on the transaction date
- Compare market movements to transaction patterns in the same currency
- Build currency exposure dashboards

### Cross-Domain Report Examples (Power BI)

| Report | Facts Used | Shared Dimension |
|--------|-----------|-----------------|
| Transaction volume overlaid with market index movement | `fact_transactions` + `fact_daily_prices` | `dim_dates` |
| Currency exposure: txn amounts vs. exchange rate trends | `fact_transactions` + `fact_exchange_rates` | `dim_dates` + `dim_currencies` |
| Days with highest volatility vs. highest fraud rate | `fact_transactions` + `fact_daily_prices` | `dim_dates` |
| Monthly revenue in base currency (EUR) using actual rates | `fact_transactions` + `fact_exchange_rates` | `dim_dates` + `dim_currencies` |

### Drill-Across Query Pattern

```sql
SELECT
    d.month,
    d.year,
    SUM(t.amount)   AS total_transaction_volume,
    AVG(p.close)    AS avg_market_close,
    AVG(e.rate)     AS avg_exchange_rate
FROM dim_dates d
LEFT JOIN fact_transactions t   ON d.date_key = t.date_key
LEFT JOIN fact_daily_prices p   ON d.date_key = p.date_key
LEFT JOIN fact_exchange_rates e ON d.date_key = e.date_key
GROUP BY d.month, d.year
```

> Power BI does this automatically when measures from different facts are placed on the same visual, as long as they share conformed dimensions.

### Design Rules

1. Conformed dimensions must be identical — same surrogate keys, same attributes, built from the same dbt model
2. Never join fact to fact — always go through shared dimensions
3. Each fact has its own grain — don't mix transaction-level with daily-level in one table
4. `fact_exchange_rates` is the enabler — makes currency normalization possible across domains
5. Date spine is king — `dim_dates` is the most important conformed dimension

### Interview-Ready Statement

> *"My Gold layer has three fact tables from two business domains — banking transactions and market data. They can be analyzed together through conformed dimensions, specifically a shared date spine and a shared currency dimension. This enables cross-domain analytics like correlating transaction volumes with market volatility, or converting all transactions to a base currency using actual daily exchange rates. This is standard Kimball drill-across design."*

---

## 24. Data Sources – Datasets & APIs

### Source 1: Banking Transactions (CSV – Kaggle)

**Dataset**: Credit Card Transactions (Fraud Detection)
**URL**: https://www.kaggle.com/datasets/kartik2112/fraud-detection
**Records**: ~1.8M transactions
**Format**: CSV download
**Contents**: Credit card transactions with merchant, category, amount, timestamp, fraud labels, customer info

Feeds into:
- `fact_transactions`
- `dim_customers` (SCD2)
- `dim_merchants`

Why selected:
- Realistic transactional data with fraud labels for KPI dashboards
- Customer + merchant dimensions naturally present
- Substantial volume (~1.8M rows) — demonstrates incremental loading
- Rich enough for segmentation, fraud analysis, transaction analytics

### Source 2: Stock / Market Prices (API – Yahoo Finance)

**Tool**: `yfinance` Python library
**URL**: https://pypi.org/project/yfinance/
**Cost**: Free, no API key needed
**Data**: Daily OHLCV (Open, High, Low, Close, Volume) for any ticker, global markets
**Historical depth**: Decades of history available

Target tickers (representative portfolio):
```
US Tech:     AAPL, MSFT
US Banks:    JPM, GS
EU Banks:    HSBA.L, BNP.PA
EU Blue Chip: SAP.DE, NOVN.SW
FX Pairs:    EUR=X, GBP=X
```

Feeds into:
- `fact_daily_prices`
- `dim_securities`
- `dim_exchanges`

Why selected:
- Completely free, no registration
- Python library makes ingestion clean
- Global coverage enables multi-market, multi-currency analysis
- Incremental by nature (new daily data)

### Source 3: Exchange Rates (REST API – frankfurter.app)

**API**: frankfurter.app (backed by ECB official reference rates)
**URL**: https://api.frankfurter.app
**Cost**: Free, no API key, no registration
**Data**: Daily exchange rates, 160+ currencies
**Example call**: `https://api.frankfurter.app/2024-01-01?from=EUR&to=USD,GBP,CHF`

Feeds into:
- `fact_exchange_rates`
- `dim_currencies`

Why selected:
- Official ECB data — credible for a finance portfolio
- Clean REST API — simple to demonstrate API ingestion
- No rate limits — reliable for development
- European-centric (EUR base) — aligns with project positioning

### Sources Summary

| Source | Type | Ingestion Method | Feeds Into |
|--------|------|-----------------|-----------|
| Kaggle Credit Card Transactions | CSV download | Python script | `fact_transactions`, `dim_customers`, `dim_merchants` |
| Yahoo Finance (yfinance) | Python API library | Python script | `fact_daily_prices`, `dim_securities`, `dim_exchanges` |
| frankfurter.app (ECB rates) | REST API | Python script | `fact_exchange_rates`, `dim_currencies` |

### Source Properties

All three sources are:
- ✅ Free — no paid subscriptions
- ✅ Reliable — public / official data
- ✅ Diverse — CSV + Python library + REST API (demonstrates range of ingestion skills)
- ✅ Incrementally loadable — all support date-based extraction
- ✅ Sufficient volume — meaningful for performance and incremental loading demos

### Shared Dimension Sources

| Conformed Dimension | Built From |
|--------------------|-----------|
| `dim_dates` | Generated date spine (dbt utility) |
| `dim_currencies` | Exchange rates API + transaction currency codes |

---

## 25. Implementation Plan

A detailed implementation plan has been created as a separate document:

> **`docs/implementation_plan.md`**

### Build Phases Summary

| Phase | Name | Key Deliverable |
|-------|------|----------------|
| 0 | Scaffolding | Repository structure, dependencies, dbt init |
| 1 | Snowflake Infrastructure | Databases, schemas, warehouses, RBAC |
| 2 | Ingestion Layer | 3 Python scripts (CSV + 2 APIs) loading to RAW |
| 3 | dbt Transformation | Staging + Marts models, tests, docs, snapshots |
| 4 | Prefect Orchestration | Flows, scheduling, retries, end-to-end pipeline |
| 5 | Power BI Dashboards | 3 dashboards (Transactions, Market, Cross-Domain) |
| 6 | Documentation & Polish | README, diagrams, reproducible setup |

### Critical Path

```
Snowflake Account → Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4
                                                      ↓
                                                   Phase 5
                                                      ↓
                                                   Phase 6
```

Estimated total effort: ~10–14 sessions.

---

## 26. Reference Materials Added

Two dbt reference books added to `/references/dbt/` (gitignored — local only, copyrighted):
- **Analytics Engineering with SQL and dbt** — Rui Machado (O'Reilly)
- **Data Engineering with dbt** — Roberto Zagni (Packt)

Key best practices extracted and applied to Phase 3 implementation plan:
- **Zagni's Pragmatic Data Platform (PDP)**: 3-layer architecture (staging/storage → refined → delivery)
- **Zagni's STG model pattern**: CTE sequence (src_data → renamed → cleaned → hashed → final)
- **Zagni's naming conventions**: `_CODE` for business keys, `_KEY` for surrogate keys, `STG_` prefix
- **Zagni's SCD2 approach**: Snapshot with `check` strategy, ephemeral STG model feeding snapshot
- **Zagni's default records**: `-1` key for orphan handling in dimensions
- **Machado's staging rules**: 1:1 with source, views only, no joins, no aggregations, `source()` only here
- **Machado's mart rules**: Tables or incremental, minimal complexity (push to intermediate CTEs)
- **Machado's incremental pattern**: `merge` strategy, `is_incremental()` filter, `unique_key`
- **Both**: Testing pyramid (not_null + unique = key signature, relationships = referential integrity)
- **Both**: Documentation as code — column-level descriptions in YAML

---

## 27. Status

This document serves as the shared project memory for the Snowflake MDS portfolio initiative.

It captures architectural rationale, tool choices, data pattern landscape, stack alignment decisions, data domain choice, dimensional model design, cross-domain analysis strategy, data source selections, implementation plan, and dbt best practices from reference material.

**Completed: Phase 0, Phase 1, Phase 2**
**Next step: Phase 3 – dbt Transformation Layer (detailed plan ready)**

