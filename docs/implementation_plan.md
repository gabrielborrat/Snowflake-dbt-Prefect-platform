# 🚀 Implementation Plan
## Snowflake Modern Data Stack Portfolio – Build Phases

---

## Overview

This document defines the step-by-step implementation plan for the MDS portfolio project.
Each phase has clear deliverables, dependencies, and acceptance criteria.

**Build order follows the data flow**: infrastructure → ingestion → transformation → orchestration → consumption → polish.

---

## Phase 0 – Project Scaffolding

### Objective
Set up the repository structure, dependencies, and local development environment.

### Tasks

| # | Task | Detail |
|---|------|--------|
| 0.1 | Create repository structure | All top-level folders as defined in architecture |
| 0.2 | Initialize Python environment | `requirements.txt` / `pyproject.toml` with all dependencies |
| 0.3 | Initialize dbt project | `dbt init`, configure `profiles.yml` for Snowflake |
| 0.4 | Set up `.gitignore` | Exclude credentials, virtual envs, dbt artifacts |
| 0.5 | Set up `.env` template | Environment variables for Snowflake credentials, API keys |
| 0.6 | Create `Makefile` or task runner | Common commands (dbt run, prefect deploy, etc.) |

### Target Repository Structure

```
Snowflake-dbt-Prefect-platform/
│
├── README.md
├── .gitignore
├── .env.example
├── requirements.txt
│
├── docs/
│   ├── project_memory.md
│   └── implementation_plan.md
│
├── architecture/
│   └── diagrams/
│
├── snowflake/
│   ├── setup/
│   │   ├── 01_databases_and_schemas.sql
│   │   ├── 02_warehouses.sql
│   │   ├── 03_roles_and_grants.sql
│   │   └── 04_file_formats_and_stages.sql
│   └── maintenance/
│       └── cost_monitoring.sql
│
├── ingestion/
│   ├── __init__.py
│   ├── config.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── snowflake_connector.py
│   │   └── logging_config.py
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── ingest_transactions.py
│   │   ├── ingest_market_prices.py
│   │   └── ingest_exchange_rates.py
│   └── tests/
│       └── test_ingestion.py
│
├── dbt_project/
│   ├── dbt_project.yml
│   ├── packages.yml
│   ├── profiles.yml (gitignored, template in .env.example)
│   ├── models/
│   │   ├── staging/
│   │   │   ├── stg_transactions.sql
│   │   │   ├── stg_market_prices.sql
│   │   │   ├── stg_exchange_rates.sql
│   │   │   └── staging.yml
│   │   └── marts/
│   │       ├── facts/
│   │       │   ├── fact_transactions.sql
│   │       │   ├── fact_daily_prices.sql
│   │       │   ├── fact_exchange_rates.sql
│   │       │   └── facts.yml
│   │       └── dims/
│   │           ├── dim_dates.sql
│   │           ├── dim_currencies.sql
│   │           ├── dim_customers.sql
│   │           ├── dim_merchants.sql
│   │           ├── dim_securities.sql
│   │           └── dims.yml
│   ├── snapshots/
│   │   └── snap_customers.sql
│   ├── macros/
│   │   └── generate_surrogate_key.sql
│   ├── seeds/
│   │   └── currency_codes.csv
│   └── tests/
│       └── generic/
│
├── orchestration/
│   ├── __init__.py
│   ├── flows/
│   │   ├── ingestion_flow.py
│   │   ├── dbt_flow.py
│   │   └── full_pipeline_flow.py
│   └── schedules/
│       └── daily_schedule.py
│
└── dashboards/
    ├── screenshots/
    └── powerbi/
```

### Dependencies (requirements.txt)

```
# Snowflake
snowflake-connector-python>=3.0
snowflake-sqlalchemy>=1.5

# dbt
dbt-snowflake>=1.7

# Ingestion
yfinance>=0.2
requests>=2.31
pandas>=2.0

# Orchestration
prefect>=2.14

# Utilities
python-dotenv>=1.0
loguru>=0.7

# Testing
pytest>=7.0
```

### Deliverables
- [ ] Repository scaffolded with all folders
- [ ] Python virtual environment working
- [ ] dbt project initialized and connecting to Snowflake
- [ ] `.env.example` with all required variables documented

### Dependencies
- Snowflake trial account must be created first

---

## Phase 1 – Snowflake Infrastructure

### Objective
Set up all Snowflake resources: databases, schemas, warehouses, roles, and access grants.

### Design Principles & Architecture

> **Why infrastructure-as-code matters:**
> In a Modern Data Stack, the data warehouse is not just "where data lives" — it is the **foundational platform** on which everything else is built. Every subsequent phase depends on having the right databases, schemas, warehouses, roles, and permissions correctly configured. By scripting the entire Snowflake infrastructure as **SQL DDL files** stored in version control (`snowflake/setup/`), we achieve **reproducibility**: the entire infrastructure can be torn down and recreated identically from these scripts, which is essential for disaster recovery, environment promotion (dev → staging → prod), and onboarding new team members. Snowflake's unique architecture — where **storage and compute are fully decoupled** — allows us to design the infrastructure in two independent dimensions: the *data layout* (databases and schemas that organize where data lives) and the *compute strategy* (warehouses that control how much processing power each workload gets). This decoupling is what makes Snowflake fundamentally different from traditional databases and is the key enabler for our cost optimization and access control strategies.

| Principle | How We Apply |
|-----------|-------------|
| **Infrastructure-as-code** | All DDL in version-controlled SQL files (`snowflake/setup/`) |
| **Separation of storage and compute** | Databases for data layout, warehouses for processing power — independently configured |
| **Medallion architecture mapping** | `RAW` database = Bronze, `ANALYTICS.STAGING` = Silver, `ANALYTICS.MARTS` = Gold |
| **Principle of least privilege** | Each role has access to exactly what it needs — no more |
| **Cost consciousness** | XS warehouses, 60s auto-suspend, monitoring queries |
| **Schema-per-source** | Each data source gets its own schema in RAW for isolation |

---

### Sub-Phase 1.0 — Databases & Schemas

> **Why this matters:**
> The database and schema structure is the **physical manifestation of the Medallion architecture** in Snowflake. We use **two databases** — `RAW` and `ANALYTICS` — rather than one, because this creates a hard security boundary: the ingestion role can write to `RAW` but has zero access to `ANALYTICS`, and the reporting role can read from `ANALYTICS.MARTS` but cannot see raw data in `RAW`. This is not just good practice — in regulated industries (banking, finance, consulting), this separation is often a **compliance requirement**. Within the `RAW` database, we create **one schema per data source** (`TRANSACTIONS`, `MARKET_DATA`, `EXCHANGE_RATES`) rather than dumping everything into a single schema. This schema-per-source pattern provides clear ownership, makes it trivial to grant or revoke access to a specific data source, and maps cleanly to dbt's `source()` definitions in Phase 3. The `ANALYTICS` database hosts two schemas: `STAGING` (Silver layer — dbt views) and `MARTS` (Gold layer — dbt tables and incremental models). Every `CREATE` statement uses `IF NOT EXISTS` to make the scripts **idempotent** — they can be re-run safely without errors, a pattern that carries through to every phase of this project. Comments on every database and schema serve as living documentation visible directly in the Snowflake UI.

| # | Task | SQL File | Detail |
|---|------|----------|--------|
| 1.0.1 | Create `RAW` database | `01_databases_and_schemas.sql` | Bronze layer — raw ingested data from all sources |
| 1.0.2 | Create RAW schemas | `01_databases_and_schemas.sql` | `RAW.TRANSACTIONS`, `RAW.MARKET_DATA`, `RAW.EXCHANGE_RATES` — one per source |
| 1.0.3 | Create `ANALYTICS` database | `01_databases_and_schemas.sql` | Silver + Gold layers — dbt transformations and dimensional models |
| 1.0.4 | Create ANALYTICS schemas | `01_databases_and_schemas.sql` | `ANALYTICS.STAGING` (Silver), `ANALYTICS.MARTS` (Gold) |
| 1.0.5 | Verify with `SHOW` commands | `01_databases_and_schemas.sql` | `SHOW DATABASES`, `SHOW SCHEMAS` to confirm creation |

**Database & Schema Layout:**

```
SNOWFLAKE ACCOUNT
│
├── RAW (database)                    ← Bronze layer
│   ├── TRANSACTIONS (schema)         ← Credit card transaction data (Kaggle CSV)
│   ├── MARKET_DATA (schema)          ← Stock prices from yfinance API
│   └── EXCHANGE_RATES (schema)       ← FX rates from frankfurter.app API
│
└── ANALYTICS (database)              ← Silver + Gold layers
    ├── STAGING (schema)              ← dbt staging models (cleaned, standardized)
    └── MARTS (schema)                ← dbt dimensional models (facts + dims)
```

**Deliverables:**
- [ ] `RAW` and `ANALYTICS` databases created
- [ ] All 5 schemas created with descriptive comments
- [ ] `SHOW` commands confirm expected structure

---

### Sub-Phase 1.1 — Warehouses (Compute Strategy)

> **Why this matters:**
> In Snowflake, a **warehouse** is a cluster of compute resources — it has no data, only processing power. This is fundamentally different from traditional databases where storage and compute are tied together. By creating **separate warehouses for each workload** — ingestion, transformation, and reporting — we achieve three critical benefits: (1) **workload isolation** — a heavy dbt transformation run cannot slow down a Power BI dashboard query, because they use different compute clusters; (2) **cost attribution** — Snowflake's `WAREHOUSE_METERING_HISTORY` shows credit usage per warehouse, so we can see exactly how much each workload costs; (3) **right-sizing** — in production, the ingestion warehouse might need to be `MEDIUM` while the reporting warehouse stays `X-SMALL`, and these can be changed independently. All warehouses are configured as **X-Small** (1 credit/hour, the smallest available) because our data volumes don't require more. The **`AUTO_SUSPEND = 60`** setting is critical for cost control: after 60 seconds of inactivity, the warehouse shuts down and stops consuming credits. `AUTO_RESUME = TRUE` means it starts back up automatically when the next query arrives — the user experiences a 1-2 second cold start, not a manual restart. `INITIALLY_SUSPENDED = TRUE` ensures no credits are consumed at creation time. These settings together mean we only pay for **actual compute time**, not idle time — on a trial account with $400 in credits, this discipline is the difference between running out of budget in a week and having enough for the entire project.

| # | Task | SQL File | Detail |
|---|------|----------|--------|
| 1.1.1 | Create `INGESTION_WH` | `02_warehouses.sql` | XS, auto-suspend 60s, auto-resume, initially suspended |
| 1.1.2 | Create `TRANSFORM_WH` | `02_warehouses.sql` | XS, auto-suspend 60s, auto-resume, initially suspended |
| 1.1.3 | Create `REPORTING_WH` | `02_warehouses.sql` | XS, auto-suspend 60s, auto-resume, initially suspended |
| 1.1.4 | Verify with `SHOW WAREHOUSES` | `02_warehouses.sql` | Confirm all 3 warehouses exist with correct settings |

**Warehouse Strategy:**

| Warehouse | Purpose | Size | Auto-Suspend | Auto-Resume | Used By |
|-----------|---------|------|:------------:|:-----------:|---------|
| `INGESTION_WH` | Python ingestion scripts | XS (1 credit/hr) | 60s | Yes | `INGESTION_ROLE` |
| `TRANSFORM_WH` | dbt transformations | XS (1 credit/hr) | 60s | Yes | `TRANSFORM_ROLE` |
| `REPORTING_WH` | Power BI dashboards | XS (1 credit/hr) | 60s | Yes | `REPORTING_ROLE` |

**Cost implication:**
```
Scenario: dbt run takes 3 minutes → warehouse active for 3 min + 1 min (auto-suspend buffer)
Credits consumed: 4 min / 60 min × 1 credit = 0.067 credits ≈ $0.20
Versus: leaving warehouse running for 1 hour = 1 credit ≈ $3.00
Savings: 93% — auto-suspend is non-negotiable for cost control.
```

**Deliverables:**
- [ ] All 3 warehouses created with correct sizes
- [ ] Auto-suspend set to 60 seconds on all warehouses
- [ ] `INITIALLY_SUSPENDED = TRUE` confirmed (no cost at creation)

---

### Sub-Phase 1.2 — Roles & Grants (RBAC)

> **Why this matters:**
> **Role-Based Access Control (RBAC)** is not an afterthought — it is a core architectural decision that demonstrates **governance maturity**, one of the most sought-after skills in data engineering interviews for banking, consulting, and finance. The principle is simple: **every user, service, and tool connects to Snowflake as a specific role, and that role has access to exactly what it needs — nothing more** (the Principle of Least Privilege). We create three custom roles that map directly to our pipeline stages: `INGESTION_ROLE` can write to `RAW` but cannot touch `ANALYTICS`; `TRANSFORM_ROLE` can read from `RAW` and write to `ANALYTICS` but cannot modify raw data; `REPORTING_ROLE` can only read from `ANALYTICS.MARTS` — it cannot see staging models, raw data, or any intermediate artifacts. All three roles are granted to `SYSADMIN` (Snowflake's administrative role hierarchy), which ensures that an admin can always manage all objects without needing `ACCOUNTADMIN`. The grant strategy uses both `ALL` (for existing objects) and `FUTURE` (for objects not yet created) grants — this is critical because dbt creates new tables and views dynamically during `dbt run`, and without `FUTURE` grants, the `REPORTING_ROLE` wouldn't be able to see newly created mart tables until someone manually runs a grant. In a production environment, this RBAC model would extend to service accounts (one per tool), row-level security, and data masking — but for a portfolio project, the three-role model cleanly demonstrates the concept.

| # | Task | SQL File | Detail |
|---|------|----------|--------|
| 1.2.1 | Create roles | `03_roles_and_grants.sql` | `INGESTION_ROLE`, `TRANSFORM_ROLE`, `REPORTING_ROLE` (run as `SECURITYADMIN`) |
| 1.2.2 | Grant roles to SYSADMIN | `03_roles_and_grants.sql` | Role hierarchy: all custom roles inherit up to `SYSADMIN` |
| 1.2.3 | Grant warehouse usage | `03_roles_and_grants.sql` | Each role → its designated warehouse only |
| 1.2.4 | Grant INGESTION_ROLE | `03_roles_and_grants.sql` | `USAGE` on `RAW`, `CREATE TABLE` + `SELECT/INSERT/UPDATE/DELETE` on all RAW schemas |
| 1.2.5 | Grant TRANSFORM_ROLE | `03_roles_and_grants.sql` | `SELECT` on `RAW.*`, `CREATE TABLE/VIEW` + full DML on `ANALYTICS.*` |
| 1.2.6 | Grant REPORTING_ROLE | `03_roles_and_grants.sql` | `SELECT` only on `ANALYTICS.MARTS.*` (tables + views, current + future) |
| 1.2.7 | Verify grants | `03_roles_and_grants.sql` | `SHOW GRANTS TO ROLE` for each role |

**RBAC Model:**

```
ACCOUNTADMIN
    └── SYSADMIN
        ├── INGESTION_ROLE  → USAGE on RAW.*, CREATE TABLE, SELECT/INSERT/UPDATE/DELETE
        │                     Warehouse: INGESTION_WH
        │
        ├── TRANSFORM_ROLE  → SELECT on RAW.* (read), full DML on ANALYTICS.* (write)
        │                     Warehouse: TRANSFORM_WH
        │
        └── REPORTING_ROLE  → SELECT only on ANALYTICS.MARTS.* (read-only)
                              Warehouse: REPORTING_WH
```

**Key design decisions:**

| Decision | Rationale |
|----------|-----------|
| `FUTURE` grants on all roles | dbt creates objects dynamically; new tables/views auto-inherit permissions |
| `SECURITYADMIN` creates roles | Snowflake best practice — role management separated from object management |
| `SYSADMIN` manages grants | Object-level grants handled by the object-owning admin role |
| `REPORTING_ROLE` restricted to `MARTS` only | BI users should never see staging models or raw data — data exposure minimization |
| No `ACCOUNTADMIN` in daily operations | `ACCOUNTADMIN` is reserved for infrastructure changes, never for running pipelines |

**Deliverables:**
- [ ] All 3 roles created and assigned to `SYSADMIN`
- [ ] Warehouse grants verified (each role → its warehouse)
- [ ] `INGESTION_ROLE` can write to RAW, cannot see ANALYTICS
- [ ] `TRANSFORM_ROLE` can read RAW, write to ANALYTICS
- [ ] `REPORTING_ROLE` can only read ANALYTICS.MARTS
- [ ] `FUTURE` grants in place for dynamically created objects

---

### Sub-Phase 1.3 — File Formats & Stages

> **Why this matters:**
> Snowflake's **file format** and **stage** objects are the infrastructure that enables structured data loading from external files. A file format defines *how* to parse a file (delimiter, header, quoting, null handling), while a stage defines *where* files are stored for loading. By creating these as named, reusable objects rather than inline parameters in `COPY INTO` statements, we achieve consistency: every CSV load uses the same parsing rules, eliminating subtle bugs caused by mismatched format options. The `CSV_FORMAT` is configured with production-grade settings: `FIELD_OPTIONALLY_ENCLOSED_BY = '"'` handles quoted fields (essential for addresses containing commas), `NULL_IF = ('', 'NULL', 'null', 'None')` normalizes the many ways sources represent null values, `TRIM_SPACE = TRUE` strips whitespace that causes silent join failures, and `ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE` provides resilience against minor schema variations in source files. The `JSON_FORMAT` is created for potential API response caching. The internal stage (`TRANSACTIONS_STAGE`) provides a landing zone for file uploads via `PUT` — while our current ingestion scripts use direct `INSERT` via the Python connector, having a stage available enables the `COPY INTO` bulk-loading pattern, which is Snowflake's most efficient loading method and can be adopted in future optimizations.

| # | Task | SQL File | Detail |
|---|------|----------|--------|
| 1.3.1 | Create CSV file format | `04_file_formats_and_stages.sql` | `RAW.TRANSACTIONS.CSV_FORMAT` — comma-delimited, header skip, quote handling, null normalization |
| 1.3.2 | Create JSON file format | `04_file_formats_and_stages.sql` | `RAW.MARKET_DATA.JSON_FORMAT` — for potential API response storage |
| 1.3.3 | Create internal stage | `04_file_formats_and_stages.sql` | `RAW.TRANSACTIONS.TRANSACTIONS_STAGE` — landing zone for CSV uploads |
| 1.3.4 | Verify formats and stages | `04_file_formats_and_stages.sql` | `SHOW FILE FORMATS`, `SHOW STAGES` |

**File format configuration explained:**

| Setting | Value | Why |
|---------|-------|-----|
| `FIELD_DELIMITER = ','` | Comma | Standard CSV delimiter |
| `SKIP_HEADER = 1` | Skip first line | Kaggle CSV has a header row |
| `FIELD_OPTIONALLY_ENCLOSED_BY = '"'` | Double quote | Handles fields with commas inside (e.g., addresses) |
| `NULL_IF = ('', 'NULL', 'null', 'None')` | Multiple null representations | Sources are inconsistent; normalize all to SQL NULL |
| `TRIM_SPACE = TRUE` | Strip whitespace | Prevents silent join failures from trailing spaces |
| `ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE` | Permissive | Avoids hard failures if source adds/removes a column |

**Deliverables:**
- [ ] CSV and JSON file formats created
- [ ] Internal stage created for transactions
- [ ] `SHOW FILE FORMATS` and `SHOW STAGES` confirm expected objects

---

### Sub-Phase 1.4 — Cost Monitoring

> **Why this matters:**
> Snowflake's pay-per-use model is a double-edged sword: it enables infinite scale, but it also means costs can spiral if left unchecked. On a trial account ($400 in credits), cost awareness is essential — but more importantly, **demonstrating cost governance** in a portfolio project signals to hiring managers that you think like a platform engineer, not just a developer. Our cost monitoring script (`cost_monitoring.sql`) provides six pre-built queries that answer the questions every Snowflake administrator needs: *How many credits have we consumed total?* *Which warehouse is the biggest cost driver?* *What's the daily trend?* *How much budget remains?* *Are all warehouses properly configured for auto-suspend?* *What are the most expensive recent queries?* These queries use Snowflake's built-in `ACCOUNT_USAGE` views — a metadata database that Snowflake maintains automatically at no extra cost. The auto-suspend verification query is particularly valuable: it flags any warehouse with auto-suspend > 60 seconds as a cost risk, acting as a **governance guardrail**. In a production environment, these queries would be wrapped in a Snowflake Task or Prefect flow running daily, with alerts when spending exceeds a threshold — but for this project, they serve as on-demand monitoring tools.

| # | Task | SQL File | Detail |
|---|------|----------|--------|
| 1.4.1 | Total credits consumed | `cost_monitoring.sql` | `SUM(credits_used)` from `WAREHOUSE_METERING_HISTORY` |
| 1.4.2 | Credits per warehouse | `cost_monitoring.sql` | Identify which workload (ingestion, transform, reporting) costs most |
| 1.4.3 | Daily consumption trend | `cost_monitoring.sql` | Spot anomalies — did a runaway query burn credits overnight? |
| 1.4.4 | Remaining budget estimate | `cost_monitoring.sql` | `$400 - total_spent` — are we on track? |
| 1.4.5 | Auto-suspend audit | `cost_monitoring.sql` | Flag warehouses with auto-suspend > 60s as cost risks |
| 1.4.6 | Expensive query log | `cost_monitoring.sql` | Top 20 longest queries in past 7 days — identify optimization targets |

**Expected cost profile for this project:**

| Activity | Estimated Credits | Estimated Cost |
|----------|:-----------------:|:--------------:|
| Phase 2: Ingestion (3 scripts × 2-5 min) | ~0.5 credits | ~$1.50 |
| Phase 3: dbt development (many short runs) | ~1.0 credits | ~$3.00 |
| Phase 4: Orchestration testing | ~0.5 credits | ~$1.50 |
| Phase 5: Power BI queries | ~0.3 credits | ~$1.00 |
| **Total estimated** | **~2.3 credits** | **~$7.00** |

> With $400 in trial credits, we have an estimated **57× safety margin** — but monitoring remains a professional habit.

**Deliverables:**
- [ ] Cost monitoring queries available and tested
- [ ] Auto-suspend verified on all warehouses
- [ ] Baseline credit consumption recorded after initial setup

---

### Deliverables (Phase 1 — Complete)
- [ ] All SQL DDL scripts written and version-controlled in `snowflake/setup/`
- [ ] Databases and schemas created (2 databases, 5 schemas)
- [ ] Warehouses created with cost-optimized settings (XS, 60s auto-suspend)
- [ ] RBAC model implemented (3 roles with least-privilege grants + FUTURE grants)
- [ ] File formats and stages ready for data loading
- [ ] Cost monitoring queries available for ongoing budget tracking

### Dependencies
- Phase 0 complete (repo structure exists)
- Snowflake trial account active

---

## Phase 2 – Ingestion Layer (Python)

### Objective
Build three Python ingestion scripts — one per data source — loading data into Snowflake RAW schemas.

### Design Principles & Architecture

> **Why a dedicated ingestion layer matters:**
> In a Modern Data Stack, the ingestion layer is the **first line of defense** for data quality. It is the boundary between the chaotic external world (APIs that change, CSVs with inconsistent schemas, networks that fail) and the controlled internal world of the data warehouse. A well-built ingestion layer follows the **separation of concerns** principle: Snowflake handles storage and compute, dbt handles transformation, and Python handles extraction and loading. This means the ingestion scripts should do **only EL** (Extract & Load) — no business transformations, no joins, no aggregations. Raw data lands in the RAW database exactly as it came from the source, with only a metadata `_loaded_at` timestamp added for auditing. This preserves the **immutability of the Bronze layer** in the Medallion architecture: if a transformation bug is discovered later, the raw data is always available to replay from. The ingestion package is structured as a proper **Python package** (`ingestion/`) with clear module separation — shared utilities (`utils/`), per-source scripts (`sources/`), and centralized configuration (`config.py`) — making it testable, reusable, and ready for orchestration by Prefect in Phase 4.

| Principle | How We Apply |
|-----------|-------------|
| **EL only — no transformation** | Raw data lands as-is; `_loaded_at` is the only added column |
| **One script per source** | Clear ownership: `ingest_transactions.py`, `ingest_market_prices.py`, `ingest_exchange_rates.py` |
| **Shared utilities** | `snowflake_connector.py` and `logging_config.py` are reused by all scripts (DRY) |
| **Centralized configuration** | `config.py` loads all secrets and settings from `.env` via `python-dotenv` |
| **Idempotency** | Every script can be safely re-run without creating duplicates |
| **Incremental loading** | Only new data is fetched on subsequent runs (cost-efficient) |
| **Package structure** | `ingestion/` is importable by Prefect flows, not just standalone scripts |

---

### Sub-Phase 2.0 — Project Configuration & Shared Utilities

> **Why this matters:**
> Before writing a single ingestion script, we build the **shared infrastructure** that every script depends on. The `config.py` module centralizes all configuration — Snowflake credentials, schema names, API endpoints, ticker lists, and batch sizes — loaded from a `.env` file via `python-dotenv`. This means secrets never appear in code, environment-specific settings (dev vs. prod) can be swapped by changing one file, and every script reads from a single source of truth. The **Snowflake connector** (`snowflake_connector.py`) uses Python's `@contextmanager` decorator to provide connections as context managers (`with get_snowflake_connection() as conn:`), which guarantees that connections are always properly closed — even if an error occurs mid-script. This prevents connection leaks, a common issue in production data pipelines. The connector also exposes three core operations: `execute_query()` for DDL/DQL, `write_dataframe()` for batch inserts, and `merge_dataframe()` for idempotent upserts via Snowflake's `MERGE INTO` statement. The **logging utility** (`logging_config.py`) uses `loguru` rather than Python's built-in `logging` module because loguru offers structured, colored, timestamped output with zero boilerplate — each log line identifies the module, severity, and timestamp, making it trivial to debug pipeline failures from log output alone.

| # | Task | Script | Detail |
|---|------|--------|--------|
| 2.0.1 | Create `config.py` | `ingestion/config.py` | Centralized settings from `.env` — credentials, schemas, tickers, FX currencies, batch size |
| 2.0.2 | Build Snowflake connector | `ingestion/utils/snowflake_connector.py` | Context-managed connections, `execute_query()`, `write_dataframe()` (batch INSERT), `merge_dataframe()` (MERGE via temp table) |
| 2.0.3 | Build logging utility | `ingestion/utils/logging_config.py` | Structured logging with `loguru` — timestamped, colored, module-tagged output |

**Key library choices:**

| Library | Purpose | Why This Library |
|---------|---------|-----------------|
| `snowflake-connector-python` | Snowflake connectivity | Official Snowflake driver; supports parameterized queries and `executemany` for batch inserts |
| `python-dotenv` | Environment variable management | Loads `.env` into `os.environ`; keeps secrets out of code |
| `loguru` | Structured logging | Zero-config, colored, structured output; far simpler than `logging` module |
| `pandas` | DataFrame operations | Industry-standard for tabular data manipulation; bridges CSV/API → Snowflake |

**Deliverables:**
- [ ] `config.py` loading all settings from `.env`
- [ ] Snowflake connector working (context manager, batch insert, merge)
- [ ] Logging utility producing structured, timestamped output

---

### Sub-Phase 2.1 — Transaction Ingestion (CSV → Snowflake)

> **Why this matters:**
> CSV ingestion is the simplest form of data loading, but it must still be done professionally. The transaction dataset (1.85M rows across two Kaggle CSV files) is a **full-load** source — unlike APIs, there is no concept of "fetching only new records" from a static file. The idempotency strategy is therefore **TRUNCATE + INSERT**: every run clears the target table and reloads from scratch, guaranteeing that the table always reflects the exact content of the CSV files. This is safe because the source data is immutable (static files on disk). The script uses `pandas.read_csv()` for parsing, then feeds the DataFrame through the shared `write_dataframe()` utility which performs **batch inserts** (configurable via `BATCH_SIZE` in config, default 10,000 rows per batch). Batching is critical for large datasets — attempting to insert 1.85M rows in a single statement would exceed Snowflake's binding parameter limits and consume excessive memory. The script also handles a subtle but important compatibility issue: **Snowflake's Python connector doesn't accept pandas Timestamp objects directly** as bind parameters, so all datetime columns are converted to strings before upload. This kind of defensive coding is what separates production-grade ingestion from tutorial-level scripts.

| # | Task | Detail |
|---|------|--------|
| 2.1.1 | Discover CSV files | Scan `data/` directory for `fraud*.csv` files using `glob` |
| 2.1.2 | Parse and prepare DataFrame | Read CSV, standardize column names (lowercase, strip), drop index column, parse datetimes to strings, select expected columns, replace NaN with None |
| 2.1.3 | Ensure target table exists | Execute `CREATE TABLE IF NOT EXISTS` DDL (embedded in script) |
| 2.1.4 | Truncate + Insert (idempotent) | `TRUNCATE TABLE` → `write_dataframe()` in batches of 10,000 |
| 2.1.5 | Log summary | Total rows loaded across all CSV files |

**Idempotency pattern — TRUNCATE + INSERT:**
```
Run 1:  TRUNCATE → INSERT 1,852,394 rows  ✅
Run 2:  TRUNCATE → INSERT 1,852,394 rows  ✅ (same result, no duplicates)
```

**Deliverables:**
- [ ] Transaction CSV files parsed and loaded to `RAW.TRANSACTIONS.CREDIT_CARD_TRANSACTIONS`
- [ ] Script is idempotent (re-run produces identical table)
- [ ] Batch upload handles 1.85M+ rows without memory issues

---

### Sub-Phase 2.2 — Market Prices Ingestion (API → Snowflake)

> **Why this matters:**
> Unlike the static CSV, market prices arrive from a **live API** (Yahoo Finance via the `yfinance` Python library) that updates daily. This requires a fundamentally different ingestion pattern: **incremental loading**. On each run, the script queries Snowflake to find the most recent date already loaded for each ticker (`SELECT MAX(date) ... WHERE ticker = %s`), then requests only the data from the *next day* onward from the API. This minimizes API calls, reduces Snowflake compute cost, and speeds up the pipeline. The idempotency strategy is **MERGE** (upsert): data is loaded into a temporary table, then merged into the target table using `MERGE INTO ... ON (ticker, date)`. If a row with the same ticker+date already exists, it is updated; if not, it is inserted. This means re-running the script — even with overlapping date ranges — never creates duplicates. The `yfinance` library is used because it provides free, reliable access to Yahoo Finance's OHLCV (Open, High, Low, Close, Volume) data without requiring an API key, and returns data as a pandas DataFrame — a natural fit for our `merge_dataframe()` utility. The script processes multiple tickers (8 by default: US tech, US banks, EU banks, EU blue chips) in a loop, with per-ticker error handling so that a failure on one ticker doesn't abort the entire ingestion.

| # | Task | Detail |
|---|------|--------|
| 2.2.1 | Query last loaded date per ticker | `SELECT MAX(date)` from Snowflake, default to `2020-01-01` if empty |
| 2.2.2 | Fetch OHLCV from Yahoo Finance | `yf.Ticker(symbol).history(start, end, auto_adjust=False)` |
| 2.2.3 | Standardize DataFrame | Lowercase columns, add `ticker` column, convert date, select expected columns |
| 2.2.4 | MERGE into target | `merge_dataframe()` with `merge_keys=['ticker', 'date']` — upsert via temp table |
| 2.2.5 | Loop over all tickers | Per-ticker error isolation; log success/failure counts |

**Idempotency pattern — MERGE (upsert):**
```
Run 1:  Fetch 2020-01-01 → today  → MERGE 1,250 rows (all INSERT)    ✅
Run 2:  Fetch yesterday → today   → MERGE 1 row   (1 INSERT or UPDATE) ✅
Run 2b: Re-run same day           → MERGE 1 row   (1 UPDATE, 0 INSERT) ✅ (no duplicates)
```

**Deliverables:**
- [ ] Market prices loaded for all 8 tickers to `RAW.MARKET_DATA.DAILY_PRICES`
- [ ] Incremental logic verified (second run fetches only new dates)
- [ ] MERGE prevents duplicates on re-runs

---

### Sub-Phase 2.3 — Exchange Rates Ingestion (API → Snowflake)

> **Why this matters:**
> The exchange rates API (`frankfurter.app`) demonstrates a third ingestion variation: **incremental loading with date-range chunking**. While the `yfinance` API handles large date ranges natively, many real-world APIs impose rate limits or response size caps. To handle this robustly, the exchange rates script splits large date ranges into **365-day chunks**, fetching and merging each chunk sequentially. This is a production pattern commonly seen in enterprise data pipelines — it prevents timeouts, keeps memory usage bounded, and provides natural checkpoints for logging and error recovery. The API returns ECB (European Central Bank) reference rates as a nested JSON structure (`{date: {currency: rate}}`), which the script flattens into a tabular format suitable for Snowflake. The MERGE strategy uses a **composite key** of three columns (`base_currency, target_currency, date`) — more complex than the market prices MERGE, demonstrating that the pattern scales to multi-column natural keys. The `frankfurter.app` API is chosen specifically because it is free, has no authentication requirement, provides reliable ECB data, and its REST interface is clean and well-documented — ideal for a portfolio project.

| # | Task | Detail |
|---|------|--------|
| 2.3.1 | Query last loaded date | `SELECT MAX(date)` from Snowflake, default to `2020-01-01` |
| 2.3.2 | Chunk date range | Split into 365-day windows to avoid API overload |
| 2.3.3 | Fetch rates from frankfurter.app | REST GET with `from`, `to` params; parse nested JSON into rows |
| 2.3.4 | MERGE into target | `merge_dataframe()` with `merge_keys=['base_currency', 'target_currency', 'date']` |
| 2.3.5 | Advance to next chunk | Loop until all date chunks processed |

**Idempotency pattern — MERGE with composite key:**
```
Run 1:  Fetch 2020-01-01 → today  → MERGE 8,760 rows (6 currencies × 1,460 days)  ✅
Run 2:  Fetch yesterday → today   → MERGE 6 rows (6 currencies × 1 day)            ✅
Run 2b: Re-run same day           → MERGE 6 rows (all UPDATE, 0 INSERT)            ✅
```

**Deliverables:**
- [ ] Exchange rates loaded for EUR → 6 target currencies to `RAW.EXCHANGE_RATES.DAILY_RATES`
- [ ] Date chunking verified for large ranges
- [ ] Composite-key MERGE prevents duplicates

---

### Sub-Phase 2.4 — Idempotency & Incremental Loading (Cross-Cutting Patterns)

> **Why this matters:**
> **Idempotency** and **incremental loading** are the two most important properties of a production data pipeline — and they are the first things a senior data engineer will look for when reviewing your code. An **idempotent** script produces the same result no matter how many times it is run: if a Prefect flow retries after a network failure, or an operator accidentally triggers a manual run, no duplicates are created and no data is lost. We implement idempotency differently depending on the source: **TRUNCATE + INSERT** for the static CSV (because the source is immutable, a full reload is safe and simple) and **MERGE** for APIs (because we need to handle overlapping date ranges gracefully). The MERGE pattern uses Snowflake's `MERGE INTO` statement via a **temporary staging table**: data is first loaded into a temp table, then merged into the target — this avoids row-level parameterized MERGE statements which are slow and error-prone. **Incremental loading** means that only *new or changed data* is extracted from the source on each run. For APIs, this is achieved by querying `SELECT MAX(date) FROM target_table` to determine the watermark, then requesting only data after that date from the API. This reduces API calls, Snowflake compute time, and pipeline duration from minutes to seconds on subsequent runs. Together, these two patterns ensure the pipeline is **safe to retry, cheap to operate, and fast to execute** — the trifecta of production-grade data engineering.

| Pattern | Strategy | Applied To |
|---------|----------|------------|
| TRUNCATE + INSERT | Full idempotent reload | `ingest_transactions.py` (CSV, immutable source) |
| MERGE via temp table | Upsert on natural key | `ingest_market_prices.py` (MERGE on `ticker, date`) |
| MERGE via temp table (composite) | Upsert on composite key | `ingest_exchange_rates.py` (MERGE on `base_currency, target_currency, date`) |
| MAX(date) watermark | Incremental extraction | Both API scripts (fetch only data after last loaded date) |

**Deliverables:**
- [ ] All scripts verified as idempotent (re-run produces identical results)
- [ ] Incremental logic verified (second run processes only new data)

---

### Sub-Phase 2.5 — Error Handling & Resilience

> **Why this matters:**
> In production, things fail. APIs return 500 errors, networks drop, Snowflake warehouses are suspended, and CSV files are missing. A pipeline that crashes on the first error and leaves the data warehouse in an inconsistent state is worse than no pipeline at all. Our error handling strategy follows the **fail gracefully, log loudly** principle: every external call (API request, Snowflake query, file I/O) is wrapped in `try/except` blocks that catch specific exception types, log a descriptive error message with full context (ticker, date range, table name), and either retry or skip the failed item without aborting the entire run. The Snowflake connector's context manager (`@contextmanager`) guarantees connection cleanup even on exceptions — the `finally` block always closes the connection. For API scripts, errors are isolated **per-ticker** or **per-chunk** — if one ticker fails out of eight, the other seven still load successfully. The `requests` library call includes a **timeout** parameter (30 seconds) to prevent the pipeline from hanging indefinitely on an unresponsive API. These patterns are not just defensive coding — they are the difference between a pipeline that runs reliably in production for months and one that requires manual intervention every other day.

| # | Task | Detail |
|---|------|--------|
| 2.5.1 | Wrap all external calls | `try/except` around API requests, Snowflake operations, file reads |
| 2.5.2 | Per-item error isolation | One failed ticker/chunk doesn't abort the entire script |
| 2.5.3 | Connection cleanup | `@contextmanager` + `finally` block ensures connections are always closed |
| 2.5.4 | API timeout | `requests.get(..., timeout=30)` to prevent hanging |
| 2.5.5 | Descriptive error logging | Every `except` logs the operation, parameters, and full exception |

**Deliverables:**
- [ ] All scripts handle errors gracefully (no orphaned connections, no partial states)
- [ ] Per-ticker/per-chunk isolation verified
- [ ] Structured error logs include sufficient context for debugging

---

### Sub-Phase 2.6 — Ingestion Tests

> **Why this matters:**
> Even though the ingestion layer is "just" EL (no business logic), it still needs validation. Ingestion tests serve as **smoke tests** — they verify that the pipeline ran, data landed in the right table, schemas match expectations, and row counts are reasonable. These tests are especially valuable after infrastructure changes (e.g., a Snowflake role grant is revoked, a column is renamed in the source). While dbt handles data quality testing for the transformation layer (Phase 3), the ingestion tests catch issues **before** dbt even runs — if the RAW layer is empty or malformed, there's no point running `dbt build`. The test file (`test_ingestion.py`) uses basic assertions (row counts > 0, expected columns present, no fully-null rows) and can be executed with `pytest` or integrated into the Prefect orchestration flow.

| # | Task | Detail |
|---|------|--------|
| 2.6.1 | Write schema validation tests | Verify column names and types match DDL for all 3 RAW tables |
| 2.6.2 | Write row count assertions | `SELECT COUNT(*) > 0` for each table after ingestion |
| 2.6.3 | Write null-check tests | No fully-null rows in critical columns (`trans_num`, `ticker`, `base_currency`) |
| 2.6.4 | Make tests runnable with `pytest` | Standard `test_ingestion.py` in `ingestion/tests/` |

**Deliverables:**
- [ ] Basic ingestion tests written and passing
- [ ] Tests can be triggered via `pytest ingestion/tests/`

---

### RAW Table Schemas (Target)

> **Why this matters:**
> The RAW layer tables are designed to be **faithful mirrors of the source data** — no transformations, no renaming, no type conversions beyond what Snowflake requires. Every table includes a `_loaded_at` metadata column with a `DEFAULT CURRENT_TIMESTAMP()` value, which serves three purposes: (1) it provides an **audit trail** showing when each row was loaded; (2) it enables **source freshness monitoring** in dbt (`dbt source freshness` checks the `MAX(_loaded_at)` against configurable thresholds); and (3) it acts as the **incremental watermark** for the dbt staging models (the `is_incremental()` filter in Phase 3 uses `_source_loaded_at` which is derived from this column). Column types are intentionally **loose** (e.g., `VARCHAR` instead of `VARCHAR(100)`, `FLOAT` instead of `DECIMAL(10,2)`) to avoid ingestion failures due to unexpected source data — strict typing is enforced later in the dbt staging layer where we have full control.

**`RAW.TRANSACTIONS.CREDIT_CARD_TRANSACTIONS`**
```sql
CREATE TABLE IF NOT EXISTS RAW.TRANSACTIONS.CREDIT_CARD_TRANSACTIONS (
    trans_date_trans_time    TIMESTAMP,
    cc_num                  NUMBER(20,0),
    merchant                VARCHAR,
    category                VARCHAR,
    amt                     FLOAT,
    first                   VARCHAR,
    last                    VARCHAR,
    gender                  VARCHAR,
    street                  VARCHAR,
    city                    VARCHAR,
    state                   VARCHAR,
    zip                     VARCHAR,
    lat                     FLOAT,
    long                    FLOAT,
    city_pop                INTEGER,
    job                     VARCHAR,
    dob                     DATE,
    trans_num               VARCHAR,
    unix_time               NUMBER,
    merch_lat               FLOAT,
    merch_long              FLOAT,
    is_fraud                INTEGER,
    _loaded_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

**`RAW.MARKET_DATA.DAILY_PRICES`**
```sql
CREATE TABLE IF NOT EXISTS RAW.MARKET_DATA.DAILY_PRICES (
    ticker                  VARCHAR,
    date                    DATE,
    open                    FLOAT,
    high                    FLOAT,
    low                     FLOAT,
    close                   FLOAT,
    adj_close               FLOAT,
    volume                  NUMBER,
    _loaded_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

**`RAW.EXCHANGE_RATES.DAILY_RATES`**
```sql
CREATE TABLE IF NOT EXISTS RAW.EXCHANGE_RATES.DAILY_RATES (
    base_currency           VARCHAR,
    target_currency         VARCHAR,
    date                    DATE,
    rate                    FLOAT,
    _loaded_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

### Deliverables (Phase 2 — Complete)
- [ ] Snowflake connector utility working
- [ ] Logging utility producing structured output
- [ ] Transaction ingestion script loading 1.85M rows to RAW
- [ ] Market prices ingestion script loading data for 8 tickers to RAW
- [ ] Exchange rates ingestion script loading data for 6 currency pairs to RAW
- [ ] All scripts are idempotent (safe to re-run)
- [ ] All scripts support incremental loading
- [ ] Error handling isolates failures per item
- [ ] Basic ingestion tests passing

### Dependencies
- Phase 1 complete (Snowflake infrastructure exists)
- Kaggle dataset downloaded to `data/` folder
- Internet access for Yahoo Finance and frankfurter.app APIs

---

## Phase 3 – dbt Transformation Layer

### Objective
Build the full dbt project: staging models (Silver layer), mart models (Gold layer — Kimball star schema), tests, documentation, and SCD2 snapshots. This is the most technically rich phase and the centrepiece of the portfolio.

### Reference Material & Design Principles

Best practices drawn from:
- *Analytics Engineering with SQL and dbt* — Rui Machado (O'Reilly)
- *Data Engineering with dbt* — Roberto Zagni (Packt)

| Principle | Source | How We Apply |
|-----------|--------|-------------|
| **Write code for humans** (Least Surprise Principle) | Zagni Ch.6 | Consistent naming prefixes (`stg_`, `dim_`, `fact_`), consistent CTE structure |
| **Single Responsibility Principle** | Zagni Ch.6 | One model = one purpose, complexity pushed to intermediate CTEs |
| **Unidirectional dependencies** | Zagni Ch.6 | `source → staging → marts`, no reverse references |
| **`source()` only in staging** | Machado Ch.2 | All downstream models use `ref()` exclusively |
| **Staging = views, Marts = tables/incremental** | Both | Views for staging (fresh, no storage), tables/incremental for marts (performance) |
| **DRY via macros & packages** | Both | `dbt_utils` for surrogate keys, date spine, generic tests |
| **Testing as first-class citizen** | Both, Zagni Ch.9 | `not_null` + `unique` = key signature; `relationships` = referential integrity |
| **Documentation as code** | Machado Ch.2, Zagni Ch.12 | Column-level descriptions in YAML, `dbt docs generate` |

---

### Sub-Phase 3.0 — Project Configuration & Foundations ✅

> **Why this matters:**
> In dbt, the `dbt_project.yml` file is the backbone of the entire transformation layer — it defines *how* models are materialized, *where* they land in Snowflake, and *how* the project is structured. A well-configured project enforces the layered architecture (staging → marts) at the framework level, rather than relying on developer discipline alone. By assigning different materializations and target schemas per folder, we guarantee that staging models always deploy as views (zero storage cost, always fresh) while mart models deploy as tables or incremental models (optimized for BI query performance). Separating snapshots into their own schema keeps the SCD2 history isolated, making it easy to audit and reason about. Installing community packages like `dbt-utils` early avoids reinventing the wheel for surrogate keys, date spines, and generic tests — a core tenet of the DRY (Don't Repeat Yourself) principle that both reference books emphasize. Getting `dbt debug` green first ensures the Snowflake connection, role, and warehouse are all correctly wired before any model code is written.

| # | Task | Detail |
|---|------|--------|
| 3.0.1 | Create `profiles.yml` | Configure Snowflake connection for dbt (gitignored, `TRANSFORM_ROLE` + `TRANSFORM_WH`) |
| 3.0.2 | Verify connection | `dbt debug` — confirm Snowflake connectivity |
| 3.0.3 | Install packages | `dbt deps` — install `dbt-utils` |
| 3.0.4 | Refine `dbt_project.yml` | Finalize model configs, snapshot schema, seed config, vars (date ranges) |
| 3.0.5 | Run seed | `dbt seed` — load `currency_codes.csv` into Snowflake |

**Key configuration (`dbt_project.yml`) — aligned with Zagni's layer architecture:**

```yaml
models:
  mds_portfolio:
    +materialized: view                  # Default: view
    staging:                             # Silver layer (adaptation)
      +materialized: view
      +schema: staging
    marts:                               # Gold layer (delivery)
      facts:
        +materialized: incremental       # Efficient updates for large fact tables
        +schema: marts
      dims:
        +materialized: table             # Full rebuild OK for small dims
        +schema: marts

snapshots:
  mds_portfolio:
    +target_schema: snapshots            # Isolated schema for SCD2

seeds:
  mds_portfolio:
    +schema: seeds
```

**Deliverables:**
- [ ] `dbt debug` passing
- [ ] `dbt deps` successful
- [ ] `dbt seed` loads `currency_codes` into Snowflake

---

### Sub-Phase 3.1 — Sources & Column Documentation ✅

> **Why this matters:**
> In dbt, a **source** is the formal declaration of an external table that lives outside the dbt project — in our case, the RAW layer tables loaded by the Python ingestion scripts. Declaring sources in YAML (rather than hardcoding table names in SQL) gives us three powerful capabilities: (1) **lineage tracking** — dbt knows where the data comes from and can draw the full DAG from raw to mart; (2) **freshness monitoring** — by specifying a `loaded_at_field` and warn/error thresholds, `dbt source freshness` can alert us when upstream data is stale before any transformation runs; (3) **documentation** — column-level descriptions defined here propagate into `dbt docs`, making the RAW schema self-documenting for any future team member. As Machado emphasizes, `{{ source() }}` should only appear in staging models — it is the single entry point into the dbt DAG. Every downstream model uses `{{ ref() }}` instead, which keeps the dependency graph clean and unidirectional.

| # | Task | Detail |
|---|------|--------|
| 3.1.1 | Enrich source definitions | Add column-level descriptions and tests to `staging.yml` |
| 3.1.2 | Document every source column | `_loaded_at`, `trans_num`, `ticker`, `base_currency`, etc. |
| 3.1.3 | Verify source freshness | `dbt source freshness` — confirm all 3 sources pass |

**Source freshness configuration (already scaffolded, will be completed):**

| Source | `loaded_at_field` | Warn After | Error After |
|--------|-------------------|:----------:|:-----------:|
| `raw_transactions.credit_card_transactions` | `_loaded_at` | 24h | 48h |
| `raw_market_data.daily_prices` | `_loaded_at` | 24h | 48h |
| `raw_exchange_rates.daily_rates` | `_loaded_at` | 24h | 48h |

**Deliverables:**
- [ ] All source columns described in YAML
- [ ] Source freshness verified with `dbt source freshness`

---

### Sub-Phase 3.2 — Staging Models (Silver Layer) ✅

> **Why this matters:**
> Staging models are the **foundation of the entire dbt project**. They sit at the boundary between "external data we don't control" and "internal models we fully own." The architectural contract is strict: each staging model maps **1:1 to a source table**, applies only **non-destructive transformations** (renaming, casting, trimming, case-fixing), and produces a clean, consistently-named output. No joins, no aggregations, no business logic — those belong in downstream layers. This discipline follows the **Single Responsibility Principle**: a staging model's only job is to translate raw data into the project's internal vocabulary. Materializing staging as **views** is deliberate — views cost nothing to store, always reflect the latest source data, and compile instantly. The CTE pattern (`src_data → renamed → cleaned → final`) used in every staging model creates a readable, auditable pipeline within each file. This pattern, championed by both Zagni and Machado, makes code reviews effortless because every staging model follows the exact same structure. By restricting `{{ source() }}` to this layer only, we ensure that if a source schema ever changes, there is exactly **one place to update** — the staging model — and all downstream models remain untouched.

> *"The staging layer serves as the basis for modular construction of more complex data models. Each staging model has a 1:1 relationship with its data source."* — Machado, Ch.2
>
> *"The goal of the STG model is to adapt external data to how we want to see and use it in our project… without changing its meaning."* — Zagni, Ch.6

**Design Rules (enforced across all staging models):**

| Rule | Rationale |
|------|-----------|
| 1:1 mapping with source table | Machado Ch.2 — each staging model mirrors one source |
| Materialized as **view** | Cost-efficient, always fresh, no storage overhead |
| **No joins** | Zagni Ch.6 — joins belong in downstream layers |
| **No aggregations** | Machado Ch.2 — preserve row-level granularity |
| Only **hard rules** (non-destructive) | Zagni Ch.6 — renaming, casting, trimming, CASE WHEN |
| `{{ source() }}` used here **only** | Machado Ch.2 — downstream models use `{{ ref() }}` |
| Consistent **CTE pattern** | Zagni Ch.6 — `src_data → renamed → cleaned → final` |
| **STG prefix** in model name | Zagni Ch.6 — `stg_` makes layer membership crystal clear |

#### 3.2.1 — `stg_transactions`

| # | Task | Detail |
|---|------|--------|
| 3.2.1a | CTE: `src_data` | Read from `{{ source('raw_transactions', 'credit_card_transactions') }}` |
| 3.2.1b | CTE: `renamed` | Rename columns to project conventions: `trans_date_trans_time` → `transaction_at`, `cc_num` → `card_number`, `amt` → `transaction_amount`, `first` → `first_name`, `last` → `last_name`, `merch_lat` → `merchant_latitude`, `merch_long` → `merchant_longitude` |
| 3.2.1c | CTE: `cleaned` | Cast types (`transaction_amount::DECIMAL(10,2)`), extract `transaction_date` from timestamp, trim/clean `merchant` name (remove `fraud_` prefix if present), upper-case `state`, derive `customer_id` (hash of name+dob or card_number) |
| 3.2.1d | CTE: `final` | Add `_source_loaded_at` metadata column from `_loaded_at`, output all clean columns |

#### 3.2.2 — `stg_market_prices`

| # | Task | Detail |
|---|------|--------|
| 3.2.2a | CTE: `src_data` | Read from `{{ source('raw_market_data', 'daily_prices') }}` |
| 3.2.2b | CTE: `renamed` | Rename: `ticker` → `ticker_symbol`, `date` → `price_date`, `adj_close` → `adjusted_close` |
| 3.2.2c | CTE: `cleaned` | Cast numerics to `DECIMAL`, ensure `high >= low` (data quality flag), `volume` as `BIGINT` |
| 3.2.2d | CTE: `final` | Add `_source_loaded_at`, output |

#### 3.2.3 — `stg_exchange_rates`

| # | Task | Detail |
|---|------|--------|
| 3.2.3a | CTE: `src_data` | Read from `{{ source('raw_exchange_rates', 'daily_rates') }}` |
| 3.2.3b | CTE: `renamed` | Rename: `date` → `rate_date`, `rate` → `exchange_rate` |
| 3.2.3c | CTE: `cleaned` | Cast `exchange_rate::DECIMAL(12,6)`, validate `rate > 0`, upper-case currency codes |
| 3.2.3d | CTE: `final` | Add `_source_loaded_at`, output |

#### Staging Tests (in `staging.yml`)

| Model | Column | Tests |
|-------|--------|-------|
| `stg_transactions` | `trans_num` | `not_null`, `unique` |
| `stg_transactions` | `transaction_amount` | `not_null` |
| `stg_transactions` | `transaction_date` | `not_null` |
| `stg_market_prices` | `ticker_symbol`, `price_date` (composite) | `not_null`, `dbt_utils.unique_combination_of_columns` |
| `stg_market_prices` | `close_price` | `not_null` |
| `stg_exchange_rates` | `base_currency`, `target_currency`, `rate_date` (composite) | `not_null`, `dbt_utils.unique_combination_of_columns` |
| `stg_exchange_rates` | `exchange_rate` | `not_null`, `dbt_utils.expression_is_true` (> 0) |

**Deliverables:**
- [ ] 3 staging models built, all materialized as views
- [ ] `dbt run -s staging` passes
- [ ] All staging tests pass (`dbt test -s staging`)

---

### Sub-Phase 3.3 — Dimension Models (Gold Layer — Kimball Dims) ✅

> **Why this matters:**
> In Kimball dimensional modeling, **dimensions are the context** — they answer *who*, *what*, *where*, and *when* about business events. Without well-designed dimensions, fact tables are just numbers without meaning. We build dimensions as **tables** (not views) because they are relatively small in cardinality and are joined to every fact query; materializing them as tables gives the Snowflake query optimizer pre-computed statistics for faster joins. Each dimension receives a **surrogate key** — a hash-based identifier generated by `dbt_utils.generate_surrogate_key()` — which decouples the data warehouse from source system identifiers that may change, be recycled, or collide across sources. The **default record** pattern (a row with `key = '-1'` and descriptive fields like `'Unknown Customer'`) is an elegant solution to a common dimensional modeling problem: when a fact record has a missing or unmatchable foreign key, it joins to the default record instead of being silently dropped from query results. This preserves row counts and makes data quality issues visible rather than hidden. **Conformed dimensions** (`dim_dates`, `dim_currencies`) are shared across multiple fact tables — this is the Kimball mechanism that enables cross-domain analysis, allowing a Power BI user to filter transactions and market prices by the same date or currency without building complex bridge tables.

> *"Mart models are responsible for integrating and presenting business-defined entities… typically materialized as tables."* — Machado, Ch.2
>
> *"Facts tell us about what happened, while dimensions provide extra descriptive information about the entities involved in a fact."* — Zagni, Ch.6

**Design Rules:**

| Rule | Rationale |
|------|-----------|
| Materialized as **table** | Small cardinality, fast query performance for BI |
| **Surrogate keys** via `dbt_utils.generate_surrogate_key()` | Zagni Ch.13, Machado Ch.2 — stable keys independent of source |
| **Default record** for each dimension (`_key = '-1'`) | Zagni Ch.6 — handles orphan facts gracefully |
| Naming: `dim_` prefix, `_key` suffix for surrogate keys, `_code` for business keys | Zagni Ch.6 naming conventions |
| Conformed dimensions shared across facts | Kimball methodology — enables cross-domain analysis |

#### 3.3.1 — `dim_dates` (Conformed Dimension — Date Spine)

| Aspect | Detail |
|--------|--------|
| **Generation method** | `dbt_utils.date_spine(datepart='day', start_date, end_date)` |
| **Date range** | `2019-01-01` to `2026-12-31` (covers all transaction + market data) |
| **Key** | `date_key` = surrogate key from `date_day` |
| **Attributes** | `date_day`, `day_of_week`, `day_of_week_name`, `day_of_month`, `week_of_year`, `month_number`, `month_name`, `quarter`, `year`, `is_weekend`, `is_month_start`, `is_month_end`, `is_year_start`, `is_year_end` |
| **Enrichment** | `is_us_trading_day` (exclude weekends and major US holidays) |

#### 3.3.2 — `dim_currencies` (Conformed Dimension — Seed-Based)

| Aspect | Detail |
|--------|--------|
| **Source** | `ref('currency_codes')` seed |
| **Key** | `currency_key` = surrogate key from `currency_code` |
| **Attributes** | `currency_code`, `currency_name`, `region` |
| **Default record** | `currency_key = '-1'`, `currency_code = 'UNK'`, `currency_name = 'Unknown'` |

#### 3.3.3 — `dim_customers` (Domain Dimension — Transaction-Derived)

| Aspect | Detail |
|--------|--------|
| **Source** | `ref('stg_transactions')` — deduplicated by customer attributes |
| **Key** | `customer_key` = surrogate key from `card_number` (or `first_name || last_name || dob`) |
| **Attributes** | `first_name`, `last_name`, `full_name`, `gender`, `street`, `city`, `state`, `zip_code`, `latitude`, `longitude`, `job`, `date_of_birth`, `age_group` (derived bucket) |
| **SCD2** | Tracked via `snap_customers` snapshot (see Sub-Phase 3.5) |
| **Default record** | `customer_key = '-1'`, `full_name = 'Unknown Customer'` |

#### 3.3.4 — `dim_merchants` (Domain Dimension — Transaction-Derived)

| Aspect | Detail |
|--------|--------|
| **Source** | `ref('stg_transactions')` — deduplicated by merchant name |
| **Key** | `merchant_key` = surrogate key from `merchant_name` |
| **Attributes** | `merchant_name`, `category`, `merchant_latitude`, `merchant_longitude` |
| **Default record** | `merchant_key = '-1'`, `merchant_name = 'Unknown Merchant'` |

#### 3.3.5 — `dim_securities` (Domain Dimension — Market-Derived)

| Aspect | Detail |
|--------|--------|
| **Source** | `ref('stg_market_prices')` — deduplicated by ticker |
| **Key** | `security_key` = surrogate key from `ticker_symbol` |
| **Attributes** | `ticker_symbol`, `security_name` (mapped from ticker), `exchange` (derived), `sector` (derived) |
| **Default record** | `security_key = '-1'`, `ticker_symbol = 'UNK'` |

#### Dimension Tests (in `dims.yml`)

| Model | Tests |
|-------|-------|
| All dims | `not_null` + `unique` on `*_key` (Zagni: "the signature of a key") |
| `dim_dates` | `not_null` on `date_day`, `unique` on `date_day` |
| `dim_currencies` | `accepted_values` on `currency_code` (EUR, USD, GBP, CHF, JPY, CAD, AUD) |
| `dim_customers` | `accepted_values` on `gender` (M, F) |
| `dim_merchants` | `not_null` on `category` |
| `dim_securities` | `not_null` on `ticker_symbol` |

**Deliverables:**
- [ ] 5 dimension models built, all materialized as table
- [ ] Surrogate keys generated for all dims
- [ ] Default records present in all dims
- [ ] `dbt run -s dims` passes
- [ ] All dimension tests pass

---

### Sub-Phase 3.4 — Fact Models (Gold Layer — Kimball Facts) ✅

> **Why this matters:**
> Fact tables are the **heart of the star schema** — they store the quantitative measurements of business processes (transaction amounts, stock prices, exchange rates). In our project, `fact_transactions` alone holds 1.85 million rows, making a full table rebuild on every `dbt run` expensive and slow. This is why we use dbt's **incremental materialization** with the `merge` strategy: on each run, only rows that are *new since the last execution* are processed and merged into the existing table. The `is_incremental()` macro creates a conditional `WHERE` clause that filters on `_source_loaded_at`, so a re-run after an ingestion that adds 1,000 rows will only transform those 1,000 rows — not the full 1.85 million. The `merge` strategy (as opposed to `append` or `insert_overwrite`) is specifically chosen because it is **idempotent**: if the same data is processed twice, the `unique_key` constraint ensures no duplicates are created. Each fact record carries **foreign keys** pointing to the relevant dimensions — these are the joins that Power BI will use to slice and dice the data. The use of **conformed dimension keys** (`date_key`, `currency_key`) across all three fact tables is what makes cross-domain analysis possible: a single `dim_dates` filter can simultaneously constrain transactions, prices, and exchange rates.

> *"Incremental models process only new or changed data rather than all data… The incremental strategy is defined as merge, where each run merges new rows with existing rows based on the unique key."* — Machado, Ch.5
>
> *"Mart models… ensure optimal performance. If creation time is an issue, configuration as incremental can be considered."* — Machado, Ch.2

**Design Rules:**

| Rule | Rationale |
|------|-----------|
| Materialized as **incremental** (`merge` strategy) | 1.85M+ transaction rows — full rebuild is too expensive |
| `unique_key` defined on natural business key | Idempotent: re-running doesn't create duplicates |
| `is_incremental()` filter on `_source_loaded_at` | Only process new data since last run (Machado Ch.5) |
| Foreign keys to all relevant dimensions | Star schema integrity (Kimball) |
| Surrogate key as primary key | `dbt_utils.generate_surrogate_key()` on natural key columns |
| Conformed dimension keys (`date_key`, `currency_key`) | Enable cross-domain joins in Power BI |

#### 3.4.1 — `fact_transactions`

| Aspect | Detail |
|--------|--------|
| **Source** | `ref('stg_transactions')` |
| **Grain** | One row per credit card transaction |
| **Incremental strategy** | `merge` on `unique_key = 'transaction_key'` |
| **Incremental filter** | `WHERE _source_loaded_at > (SELECT MAX(_source_loaded_at) FROM {{ this }})` |
| **Primary key** | `transaction_key` = surrogate from `trans_num` |
| **Foreign keys** | `date_key` → `dim_dates`, `customer_key` → `dim_customers`, `merchant_key` → `dim_merchants`, `currency_key` → `dim_currencies` |
| **Measures** | `transaction_amount`, `is_fraud` (0/1) |
| **Degenerate dimensions** | `trans_num` (transaction number), `card_number` (masked) |

#### 3.4.2 — `fact_daily_prices`

| Aspect | Detail |
|--------|--------|
| **Source** | `ref('stg_market_prices')` |
| **Grain** | One row per security per trading day |
| **Incremental strategy** | `merge` on `unique_key = 'price_key'` |
| **Primary key** | `price_key` = surrogate from `ticker_symbol + price_date` |
| **Foreign keys** | `date_key` → `dim_dates`, `security_key` → `dim_securities`, `currency_key` → `dim_currencies` |
| **Measures** | `open_price`, `high_price`, `low_price`, `close_price`, `adjusted_close_price`, `volume`, `daily_return` (calculated: `(close - prev_close) / prev_close`) |

#### 3.4.3 — `fact_exchange_rates`

| Aspect | Detail |
|--------|--------|
| **Source** | `ref('stg_exchange_rates')` |
| **Grain** | One row per currency pair per day |
| **Incremental strategy** | `merge` on `unique_key = 'rate_key'` |
| **Primary key** | `rate_key` = surrogate from `base_currency + target_currency + rate_date` |
| **Foreign keys** | `date_key` → `dim_dates`, `base_currency_key` → `dim_currencies`, `target_currency_key` → `dim_currencies` |
| **Measures** | `exchange_rate`, `rate_change` (day-over-day delta) |

#### Fact Tests (in `facts.yml`)

| Model | Column | Tests |
|-------|--------|-------|
| All facts | `*_key` (PK) | `not_null`, `unique` |
| `fact_transactions` | `date_key` | `not_null`, `relationships` → `dim_dates` |
| `fact_transactions` | `customer_key` | `not_null`, `relationships` → `dim_customers` |
| `fact_transactions` | `merchant_key` | `not_null`, `relationships` → `dim_merchants` |
| `fact_transactions` | `transaction_amount` | `not_null`, `dbt_utils.expression_is_true` (> 0) |
| `fact_daily_prices` | `date_key` | `not_null`, `relationships` → `dim_dates` |
| `fact_daily_prices` | `security_key` | `not_null`, `relationships` → `dim_securities` |
| `fact_exchange_rates` | `date_key` | `not_null`, `relationships` → `dim_dates` |
| `fact_exchange_rates` | `base_currency_key` | `not_null`, `relationships` → `dim_currencies` |
| `fact_exchange_rates` | `target_currency_key` | `not_null`, `relationships` → `dim_currencies` |

**Deliverables:**
- [ ] 3 fact models built, all materialized as incremental (merge)
- [ ] Foreign keys reference correct dimension tables
- [ ] Incremental logic verified (`dbt run` twice produces same result)
- [ ] `dbt run --full-refresh -s facts` works for initial load
- [ ] All fact tests pass

---

### Sub-Phase 3.5 — Snapshot (SCD Type 2) ✅

> **Why this matters:**
> In the real world, dimension attributes change over time — a customer moves to a new city, changes jobs, or updates their address. A standard dimension table only stores the *current* state, which means historical analysis becomes impossible: "What was the fraud rate for customers in New York last year?" would be wrong if some of those customers have since moved to California. **Slowly Changing Dimension Type 2 (SCD2)** solves this by preserving every historical version of a dimension record, each tagged with `valid_from` and `valid_to` timestamps. dbt's built-in `snapshot` functionality automates this entirely — on each `dbt snapshot` run, it compares the current source data against the previously captured state. If any tracked columns have changed, it closes the old record (sets `dbt_valid_to`) and inserts a new version (with `dbt_valid_from = now()`). The `check` strategy (rather than `timestamp`) is chosen here because our source data doesn't have a reliable `updated_at` column — instead, dbt compares the actual column values to detect changes. Snapshots must run **before** the main `dbt run` to capture the source state before any transformations alter it. This is a pattern that demonstrates sophisticated data engineering thinking and is highly valued in interviews for analytics engineering roles.

> *"dbt provides the snapshot functionality to save incoming data… storing it in a form called Slowly Changing Dimension of type two."* — Zagni, Ch.6

#### `snap_customers`

| Configuration | Value | Rationale |
|---------------|-------|-----------|
| **Strategy** | `check` | No reliable `updated_at` in source; compare attribute columns |
| **unique_key** | `customer_id` (derived from card_number or name+dob hash) | Identity of the customer entity |
| **check_cols** | `['city', 'state', 'zip_code', 'job']` | Track relocations and career changes |
| **invalidate_hard_deletes** | `True` | Mark deleted customers as inactive |
| **target_schema** | `snapshots` | Isolated from staging/marts (Zagni Ch.6) |

**SCD2 Output Columns (auto-managed by dbt):**
- `dbt_valid_from` — when this version became active
- `dbt_valid_to` — when this version was superseded (`NULL` = current)
- `dbt_scd_id` — unique row identifier
- `dbt_updated_at` — insertion timestamp

**Execution order:** `dbt snapshot` runs BEFORE `dbt run` (Zagni Ch.6 — capture source state first).

**Deliverables:**
- [ ] `snap_customers` snapshot created and populated
- [ ] SCD2 columns present (`dbt_valid_from`, `dbt_valid_to`)
- [ ] `dbt snapshot` runs without errors

---

### Sub-Phase 3.6 — Custom Macros ✅

> **Why this matters:**
> One of dbt's most powerful features is its **macro system** — Jinja-templated SQL functions that can be reused across the entire project. Macros enforce the **DRY principle** (Don't Repeat Yourself): instead of copying the same surrogate key logic or currency conversion formula into every model, we define it once in a macro and call it everywhere. This means a change to the logic (e.g., switching from MD5 to SHA-256 for surrogate keys) only needs to happen in one place. The dbt community has already codified the most common patterns into the `dbt-utils` package, but wrapping those community macros in a project-level macro gives us an additional abstraction layer — if the upstream package ever changes its API, our models are shielded behind our own interface. Custom macros also serve as excellent portfolio talking points: they demonstrate that you think about **maintainability and scale**, not just getting a query to work once.

**Macros Inventory:**

| Macro | File | Purpose | Used In | Reference |
|-------|------|---------|---------|-----------|
| `safe_divide` | `macros/safe_divide.sql` | Division-by-zero safe division with optional rounding — returns `NULL` instead of erroring | `fact_daily_prices` (daily_return) | Zagni Ch.8 |
| `coalesce_key` | `macros/coalesce_key.sql` | Orphan fact FK protection — substitutes default key `'-1'` when dimension lookup is `NULL` | All 3 fact models (10 FK columns) | Kimball pattern |
| `cents_to_dollars` | `macros/cents_to_dollars.sql` | Converts cents → dollars (`amount / 100`) — reusable pattern for banking/payment sources | Not yet used (current dataset in dollars); included as DRY pattern demo | Machado Ch.2 |
| `generate_schema_name` | `macros/generate_schema_name.sql` | Overrides dbt's default schema naming to produce clean names (`STAGING`, `SEEDS`, `SNAPSHOTS`) | dbt framework (auto-invoked) | Created in Sub-Phase 3.0 |
| `generate_surrogate_key` | `macros/generate_surrogate_key.sql` | Documentation-only — records the convention to use `dbt_utils.generate_surrogate_key()` directly | N/A (reference doc) | Zagni Ch.8, Ch.13 |

**Design Decision — No wrapper around `dbt_utils.generate_surrogate_key()`:**
The original plan proposed wrapping it for consistency. During implementation, we decided this added unnecessary indirection — the `dbt_utils` function is already well-known, readable, and stable. We document the convention in a header file instead.

**Refactoring performed:**
- `fact_transactions.sql` — 4 × inline `COALESCE(..., '-1')` → `{{ coalesce_key(...) }}`
- `fact_daily_prices.sql` — 3 × `COALESCE` → `{{ coalesce_key() }}` + 7-line CASE block → `{{ safe_divide() }}`
- `fact_exchange_rates.sql` — 3 × `COALESCE` → `{{ coalesce_key() }}`

**Verification:**
- `dbt run --full-refresh -s marts.facts` — row counts unchanged (1,852,394 / 12,358 / 9,420) ✅
- `dbt test -s marts.facts` — 33/33 PASS ✅
- Registered macro count: 639 → 642 (+3 custom macros)

---

### Sub-Phase 3.7 — Testing Strategy ✅

> **Why this matters:**
> In production data platforms, **untested data is untrusted data**. dbt treats testing as a first-class citizen by embedding test declarations directly alongside model definitions in YAML — tests live *with* the code they validate, not in a separate QA silo. The testing strategy follows a **pyramid** pattern: at the base, **schema tests** (`not_null`, `unique`) form the "key signature" of every model — if a primary key has duplicates or nulls, the entire star schema's integrity collapses. In the middle, **generic tests** (`relationships`, `accepted_values`) verify referential integrity (every `customer_key` in `fact_transactions` must exist in `dim_customers`) and domain validity (gender must be M or F). At the top, **singular tests** (custom SQL queries in the `tests/` folder) encode specific business rules that no generic test can capture (e.g., "no transaction should have a future date"). The beauty of dbt testing is that every test returns *failing rows* — not just a pass/fail boolean — making debugging immediate. Running `dbt test` as part of the orchestration pipeline (Phase 4) means bad data is caught **before** it reaches Power BI, not after a stakeholder reports a wrong number.

> *"dbt provides a testing framework… Tests identify rows that do not meet assertion criteria."* — Machado, Ch.2
>
> *"The best way is to make data quality a real thing… define exactly what we expect as input and output and then check that the data adheres to these requirements."* — Zagni, Ch.5

**Test Pyramid:**

```
                    ┌─────────────────────┐
                    │  Singular Tests     │  ← Custom business logic
                    │  (SQL in /tests)     │     e.g. no future dates in transactions
                    ├─────────────────────┤
                    │  Generic Tests      │  ← Relationships, accepted_values
                    │  (YAML declared)     │     referential integrity across star schema
                    ├─────────────────────┤
                    │  Schema Tests       │  ← not_null, unique
                    │  (YAML declared)     │     key signatures for every model
                    └─────────────────────┘
                    ← Coverage increases downward →
```

**Generic Tests (YAML-declared, built across Sub-Phases 3.1–3.4):**

| Layer | YAML File | Test Types | Count |
|-------|-----------|------------|-------|
| Sources (RAW) | `staging.yml` | `not_null`, `unique`, `accepted_values` | 10 |
| Staging (Silver) | `staging.yml` | `not_null`, `unique`, `accepted_values` | 16 |
| Dimensions (Gold) | `dims.yml` | `not_null`, `unique`, `accepted_values` | 17 |
| Facts (Gold) | `facts.yml` | `not_null`, `unique`, `relationships`, `accepted_values` | 33 |
| **Total generic** | | | **76** |

**Singular Tests (custom SQL in `tests/`):**

| Test | What It Validates | Layer |
|------|-------------------|-------|
| `assert_no_future_transactions.sql` | No `transaction_date > CURRENT_DATE()` — catches timezone or ingestion bugs | `fact_transactions` |
| `assert_positive_prices.sql` | `close_price > 0` — a stock cannot have zero or negative close | `fact_daily_prices` |
| `assert_exchange_rates_positive.sql` | `exchange_rate > 0` — a FX rate cannot be zero or negative | `fact_exchange_rates` |
| `assert_fact_transaction_amount_matches_staging.sql` | Row count in fact = row count in staging — reconciliation sanity check | `fact_transactions` vs `stg_transactions` |

Singular tests return *failing rows*. If 0 rows returned → PASS. If any rows returned → FAIL with the offending data visible for debugging.

**Test Execution:**
```bash
dbt test                           # All tests (76 generic + 4 singular)
dbt test -s staging                # Only staging tests
dbt test -s tag:relationships      # Only referential integrity
dbt source freshness               # Source freshness checks (3 sources)
```

**Verification:**
- `dbt test` → **80/80 PASS** (76 generic + 4 singular), 0 warnings ✅
- `dbt source freshness` → **3/3 PASS** ✅

**Deliverables:**
- [x] Generic tests declared for all models in YAML (not_null, unique, relationships, accepted_values) — 76 tests
- [x] 4 singular tests written and passing
- [x] `dbt test` returns 0 failures — **80/80 PASS**
- [x] Source freshness passing — **3/3 PASS**

---

### Sub-Phase 3.8 — Documentation

> **Why this matters:**
> In traditional data warehousing, documentation is an afterthought — a Word document or wiki page that goes stale within weeks. dbt fundamentally changes this by treating **documentation as code**: model and column descriptions live in the same YAML files as tests and configurations, are version-controlled in Git, and are compiled into a rich, interactive website with `dbt docs generate`. The crown jewel is the **DAG lineage graph** — a visual representation of every model, source, and dependency in the project. This graph is invaluable for onboarding new team members, debugging pipeline failures ("what upstream model feeds this mart?"), and demonstrating architectural clarity to hiring managers. When a consulting manager reviews this project, the DAG instantly communicates: "this candidate understands data flow, dependency management, and layered architecture." Column-level descriptions also propagate into BI tools, meaning a Power BI user hovering over a field can see its definition without leaving their report. For our portfolio, the DAG screenshot will be one of the most impactful visual artifacts in the README.

> *"dbt advocates for documenting data models and transformations as code."* — Machado, Ch.4
>
> *"Lineage graph… dbt-generated documentation… Source freshness report… Exposures"* — Zagni, Ch.12

| # | Task | Detail |
|---|------|--------|
| 3.8.1 | Column-level descriptions | Every column in every model described in YAML |
| 3.8.2 | Model-level descriptions | Business purpose for each staging, dim, and fact model |
| 3.8.3 | Generate docs | `dbt docs generate` |
| 3.8.4 | Verify DAG | `dbt docs serve` — inspect full lineage graph |
| 3.8.5 | Screenshot DAG | Save to `architecture/diagrams/` for README |

**Deliverables:**
- [ ] All models and columns documented in YAML
- [ ] `dbt docs generate` runs successfully
- [ ] DAG lineage graph verified (no orphans, no reverse dependencies)
- [ ] DAG screenshot saved

---

### Full Model Dependency Graph (DAG)

```
                     ┌──────────────────────────────────────┐
                     │           SOURCES (RAW)               │
                     │                                        │
                     │  raw_transactions                      │
                     │  raw_market_data                       │
                     │  raw_exchange_rates                    │
                     │  currency_codes (seed)                 │
                     └──────┬───────┬───────┬───────┬────────┘
                            │       │       │       │
                     ┌──────▼───────▼───────▼──┐    │
                     │    STAGING (Silver)       │    │
                     │                           │    │
                     │  stg_transactions         │    │
                     │  stg_market_prices         │    │
                     │  stg_exchange_rates        │    │
                     └──────┬───────┬───────┬────┘    │
                            │       │       │         │
               ┌────────────┼───────┼───────┼─────────┤
               │            │       │       │         │
        ┌──────▼──────┐ ┌──▼───┐ ┌─▼──┐ ┌──▼───┐ ┌───▼──────────┐
        │snap_customers│ │dim_  │ │dim_│ │dim_  │ │dim_currencies│
        │ (SCD2)       │ │custs │ │sec │ │merch │ │(from seed)   │
        └──────┬───────┘ └──┬───┘ └──┬─┘ └──┬───┘ └───┬──────────┘
               │            │        │      │         │
               │    ┌───────┴────────┴──────┴─────────┤
               │    │                                   │
               │    │         dim_dates (date spine)     │
               │    │                                   │
               │    └───────┬────────┬──────┬───────────┘
               │            │        │      │
        ┌──────▼────────────▼──┐ ┌───▼──┐ ┌─▼────────────────┐
        │  fact_transactions    │ │fact_ │ │fact_exchange_rates│
        │  (incremental, merge) │ │daily │ │(incremental)      │
        └───────────────────────┘ │price │ └───────────────────┘
                                  │(inc.)│
                                  └──────┘
```

### Materialization Summary

| Layer | Models | Materialization | Schema |
|-------|--------|:---------------:|--------|
| Staging (Silver) | `stg_transactions`, `stg_market_prices`, `stg_exchange_rates` | `view` | `ANALYTICS.STAGING` |
| Dimensions (Gold) | `dim_dates`, `dim_currencies`, `dim_customers`, `dim_merchants`, `dim_securities` | `table` | `ANALYTICS.MARTS` |
| Facts (Gold) | `fact_transactions`, `fact_daily_prices`, `fact_exchange_rates` | `incremental` (merge) | `ANALYTICS.MARTS` |
| Snapshots | `snap_customers` | `table` (SCD2) | `ANALYTICS.SNAPSHOTS` |
| Seeds | `currency_codes` | `table` | `ANALYTICS.SEEDS` |

### Execution Order

Following Zagni's recommended ELT pattern:

```bash
# 1. Capture source state (SCD2)
dbt snapshot

# 2. Build staging layer (views)
dbt run -s staging

# 3. Build seeds
dbt seed

# 4. Build dimensions (must exist before facts)
dbt run -s dims

# 5. Build facts (reference dims via foreign keys)
dbt run -s facts

# 6. Run all tests
dbt test

# OR — single command (recommended):
dbt build    # runs snapshot + seed + run + test in correct DAG order
```

### Naming Conventions

| Convention | Example | Source |
|------------|---------|--------|
| `stg_` prefix for staging | `stg_transactions` | Zagni Ch.6 |
| `dim_` prefix for dimensions | `dim_customers` | Kimball standard |
| `fact_` prefix for facts | `fact_transactions` | Kimball standard |
| `snap_` prefix for snapshots | `snap_customers` | Project convention |
| `_key` suffix for surrogate keys | `customer_key` | Zagni Ch.6 |
| `_code` suffix for business identifiers | `currency_code` | Zagni Ch.6 |
| `_at` suffix for timestamps | `transaction_at` | dbt community convention |
| `_date` suffix for dates | `transaction_date` | dbt community convention |
| `is_` prefix for booleans | `is_fraud`, `is_weekend` | dbt community convention |

### Estimated Effort for Phase 3

| Sub-Phase | Sessions | Hours | Notes |
|-----------|:--------:|:-----:|-------|
| 3.0 Configuration | 0.5 | 1–2h | profiles.yml, dbt debug, dbt deps, dbt seed |
| 3.1 Sources | 0.5 | 1–2h | Column descriptions, freshness |
| 3.2 Staging models | 1 | 2–3h | 3 models with CTE pattern + tests |
| 3.3 Dimensions | 1–1.5 | 3–5h | 5 models, date spine, default records, surrogate keys |
| 3.4 Facts | 1–1.5 | 3–5h | 3 incremental models, FK lookups, calculated measures |
| 3.5 Snapshot | 0.5 | 1h | snap_customers with check strategy |
| 3.6 Macros | 0.25 | 0.5h | Surrogate key wrapper |
| 3.7 Testing | 0.5 | 1–2h | Singular tests, verify all generic tests |
| 3.8 Documentation | 0.5 | 1–2h | Column descriptions, dbt docs generate, DAG screenshot |
| **Total** | **~5–7** | **~14–22h** | **The marathon phase** |

### Deliverables Checklist

- [ ] `dbt debug` passing (Snowflake connection verified)
- [ ] `dbt deps` successful (dbt-utils installed)
- [ ] `dbt seed` loads currency_codes
- [ ] Source freshness passing (`dbt source freshness`)
- [ ] 3 staging models built as views
- [ ] 5 dimension models built as tables (with surrogate keys + default records)
- [ ] 3 fact models built as incremental (merge strategy)
- [ ] 1 SCD2 snapshot (`snap_customers`) working
- [ ] All generic tests passing (not_null, unique, relationships, accepted_values)
- [ ] 4+ singular tests passing (business logic validation)
- [ ] All models and columns documented in YAML
- [ ] `dbt docs generate` successful
- [ ] DAG lineage verified (no orphans, clean unidirectional flow)
- [ ] `dbt build` (full pipeline) completes without errors

### Dependencies
- Phase 2 complete (RAW tables populated with data) ✅

---

## Phase 4 – Prefect Orchestration

### Objective
Orchestrate the full pipeline — ingestion, dbt runs, tests — using Prefect flows with scheduling, retries, and logging.

### Tasks

| # | Task | Detail |
|---|------|--------|
| 4.1 | Create ingestion flow | Orchestrate all three ingestion scripts as Prefect tasks |
| 4.2 | Create dbt flow | Run `dbt run` + `dbt test` as Prefect tasks |
| 4.3 | Create full pipeline flow | Chain ingestion → dbt → validation |
| 4.4 | Add retry logic | Retries on API calls and Snowflake connections |
| 4.5 | Add logging | Structured logging within Prefect flows |
| 4.6 | Add scheduling | Daily schedule for incremental runs |
| 4.7 | Add error notifications | Log failures clearly (Prefect UI or console) |
| 4.8 | Test end-to-end pipeline | Run full flow and verify data in all layers |

### Flow Architecture

```
full_pipeline_flow (daily schedule)
│
├── Task: ingest_transactions()
├── Task: ingest_market_prices()
├── Task: ingest_exchange_rates()
│
├── Task: dbt_run_staging()
├── Task: dbt_run_marts()
│
├── Task: dbt_test()
│
└── Task: log_pipeline_summary()
```

### Flow Configuration

| Parameter | Value |
|-----------|-------|
| Schedule | Daily at 06:00 UTC |
| Retries | 3 (on ingestion tasks) |
| Retry delay | 60 seconds |
| Timeout | 30 minutes per task |
| Concurrency | Ingestion tasks run in parallel, dbt tasks sequential |

### Deliverables
- [ ] Ingestion flow working
- [ ] dbt flow working
- [ ] Full pipeline flow chaining both
- [ ] Retry logic verified
- [ ] Daily schedule configured
- [ ] End-to-end pipeline tested
- [ ] Prefect UI showing successful runs

### Dependencies
- Phase 2 complete (ingestion scripts working)
- Phase 3 complete (dbt models working)

---

## Phase 5 – Power BI Consumption Layer

### Objective
Build dashboards that demonstrate business value from both domains, including cross-domain analytics.

### Tasks

| # | Task | Detail |
|---|------|--------|
| 5.1 | Connect Power BI to Snowflake | Use `REPORTING_ROLE` + `REPORTING_WH` |
| 5.2 | Import star schema | Import all facts + dimensions from MARTS |
| 5.3 | Build Transaction Analytics dashboard | Volume, fraud rate, category breakdown |
| 5.4 | Build Market Analytics dashboard | Price trends, volatility, sector performance |
| 5.5 | Build Cross-Domain dashboard | Transaction volume vs. market movement, currency exposure |
| 5.6 | Define KPI measures | DAX measures for all key metrics |
| 5.7 | Take screenshots | For README and portfolio presentation |

### Dashboard Plan

**Dashboard 1: Transaction Analytics**
- Total transaction volume (daily / monthly)
- Fraud rate trend
- Top merchant categories
- Geographic heatmap
- Customer segmentation

**Dashboard 2: Market Analytics**
- Stock price trends (multi-ticker)
- Daily returns / volatility
- Sector comparison
- Volume analysis
- Trading calendar alignment

**Dashboard 3: Cross-Domain Intelligence**
- Transaction volume overlaid with market index
- Currency exposure: transaction amounts vs. FX rate trends
- Monthly revenue in EUR (converted via actual daily rates)
- Correlation analysis: market volatility vs. transaction patterns

### Deliverables
- [ ] Power BI connected to Snowflake via REPORTING_ROLE
- [ ] Transaction Analytics dashboard built
- [ ] Market Analytics dashboard built
- [ ] Cross-Domain Intelligence dashboard built
- [ ] Screenshots captured for documentation
- [ ] KPI definitions documented

### Dependencies
- Phase 3 complete (MARTS layer populated)
- Phase 1 RBAC working (REPORTING_ROLE can access MARTS)

---

## Phase 6 – Documentation & Polish

### Objective
Finalize all documentation, clean up code, and prepare the repository for portfolio presentation.

### Tasks

| # | Task | Detail |
|---|------|--------|
| 6.1 | Write README.md | Project overview, architecture diagram, setup instructions |
| 6.2 | Add architecture diagrams | Visual representation of the full pipeline |
| 6.3 | Document setup instructions | Step-by-step to reproduce the project |
| 6.4 | Clean up code | Consistent formatting, remove dead code, add docstrings |
| 6.5 | Verify dbt docs | Ensure all models and columns are documented |
| 6.6 | Final end-to-end test | Full pipeline run from scratch |
| 6.7 | Cost report | Document Snowflake credit usage |

### Deliverables
- [ ] README.md complete and professional
- [ ] Architecture diagrams included
- [ ] Reproducible setup instructions
- [ ] Code clean and well-documented
- [ ] dbt docs complete
- [ ] Final pipeline run successful
- [ ] Cost report included

### Dependencies
- All previous phases complete

---

## Build Order Summary

```
Phase 0: Scaffolding        ██░░░░░░░░░░  (foundation)
Phase 1: Snowflake Setup    ████░░░░░░░░  (infrastructure)
Phase 2: Ingestion          ██████░░░░░░  (data acquisition)
Phase 3: dbt Transformation ████████░░░░  (modeling)
Phase 4: Prefect Orchestration ██████████░░  (automation)
Phase 5: Power BI           ████████████  (consumption)
Phase 6: Documentation      ████████████  (polish)
```

### Critical Path

```
Snowflake Account → Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4
                                                      ↓
                                                   Phase 5
                                                      ↓
                                                   Phase 6
```

> Phase 4 (Prefect) and Phase 5 (Power BI) can be worked on in parallel once Phase 3 is complete.

---

## Estimated Effort

### Development Approach: AI-Driven Development

This project follows an **AI-driven development** workflow: the AI writes code, the engineer reviews, validates, and runs. This is the standard senior-level approach in 2026 — the engineer acts as **architect and reviewer**, directing the AI on *what* to build and *why*, while the AI handles the mechanical code generation. The value is in the architectural decisions, not the keystrokes.

> *"A senior architect doesn't lay every brick — they design the building, choose the materials, validate the structural integrity, and make sure it meets code."*

### Effort Estimates (AI-Driven Pace)

A **session** = ~1–2 hours of focused work (review, run, ask questions, iterate).

| Phase | Sessions | Hours (approx.) | Solo Estimate | What Determines Duration |
|-------|:--------:|:----------------:|:-------------:|--------------------------|
| Phase 0 – Scaffolding | ½ | ~30min | 2–3h | AI generates structure, engineer reviews |
| Phase 1 – Snowflake | ½ | ~30min | 2–3h | SQL DDL generated, engineer executes in Snowflake |
| Phase 2 – Ingestion | 1 | 1–2h | 6–10h | AI writes scripts, engineer debugs connections |
| Phase 3 – dbt | 2–3 | 3–5h | 8–14h | **Heaviest phase** — but AI handles SQL, engineer validates logic |
| Phase 4 – Prefect | 1 | 1–2h | 3–6h | Wiring existing scripts into flows |
| Phase 5 – Power BI | 1–2 | 3–6h | 3–6h | **Same** — dashboard design requires manual UI work |
| Phase 6 – Docs | ½ | ~1h | 2–3h | AI generates, engineer polishes |
| **Total** | **6–8** | **~10–17h** | ~26–45h | **~60% faster with AI-driven approach** |

### Calendar Estimates by Pace

| Pace | Schedule | Timeline |
|------|----------|----------|
| Intense | ~3h/day | ~4–6 days |
| Steady | ~1.5h/day | ~1–1.5 weeks |
| Weekend warrior | ~4–6h on weekends | ~2 weekends |

### Where the Engineer's Time Goes (AI-Driven)

| Activity | % of Time | Why It Matters |
|----------|:---------:|---------------|
| **Reviewing generated code** | 30% | Catch errors, validate logic, ensure quality |
| **Understanding concepts** | 25% | Asking "why?", building interview readiness |
| **Running & debugging** | 20% | Executing commands, resolving environment issues |
| **Architectural decisions** | 15% | Choosing patterns, validating trade-offs |
| **Documentation review** | 10% | Ensuring the project tells a coherent story |

### Speed Factors

- **Faster**: AI writes code, engineer reviews — mechanical work is eliminated
- **Slower (intentionally)**: Deep-diving into concepts like we did for dbt architecture — this is *investment time* that pays off in interviews
- **Same speed regardless**: Power BI dashboards (manual UI), Snowflake SQL execution (manual)
- **Phase 3 (dbt) remains the marathon** — even with AI, the modeling decisions require careful thought

---

## Current Status

- [x] Architecture designed (Medallion + Kimball)
- [x] Stack selected (Snowflake + dbt + Prefect + Python + Power BI)
- [x] Data domain chosen (Banking Transactions + Market Data)
- [x] Dimensional model designed (3 facts, 7 dimensions, 2 conformed)
- [x] Data sources selected (Kaggle CSV + yfinance + frankfurter.app)
- [x] Implementation plan defined
- [x] **Phase 0 – Scaffolding** ✅ Complete
  - [x] Repository folder structure created (all directories)
  - [x] `requirements.txt` with all dependencies
  - [x] `.gitignore` configured
  - [x] `.env.example` template with all variables
  - [x] `Makefile` with common commands
  - [x] dbt project initialized (`dbt_project.yml`, `packages.yml`, sources, model placeholders)
  - [x] Python ingestion package structure (`config.py`, connectors, source scripts)
  - [x] Orchestration package structure (flows, schedules)
  - [x] Snowflake SQL scripts scaffolded (setup + maintenance)
  - [x] Currency seed file (`currency_codes.csv`)
- [x] **Phase 1 – Snowflake Infrastructure** ✅ Complete
  - [x] `01_databases_and_schemas.sql` — RAW + ANALYTICS databases, 5 schemas
  - [x] `02_warehouses.sql` — 3 warehouses (XS, 60s auto-suspend)
  - [x] `03_roles_and_grants.sql` — RBAC: INGESTION/TRANSFORM/REPORTING roles + grants
  - [x] `04_file_formats_and_stages.sql` — CSV + JSON formats, internal stage
  - [x] `cost_monitoring.sql` — 6 monitoring queries (credits, daily trend, remaining budget)
  - [x] All scripts executed in Snowflake ✅
  - [x] User grants applied ✅
- [x] **Phase 2 – Ingestion Layer** ✅ Complete
  - [x] Python venv created, all dependencies installed
  - [x] Snowflake connector utility (`snowflake_connector.py`) — connection manager, write_dataframe, merge_dataframe
  - [x] Logging utility (`logging_config.py`) — structured loguru output
  - [x] Ingestion config (`config.py`) — centralized settings, tickers, currencies
  - [x] `ingest_exchange_rates.py` — frankfurter.app API → 9,438 rows loaded ✅
  - [x] `ingest_market_prices.py` — yfinance API (8 tickers) → 12,358 rows loaded ✅
  - [x] `ingest_transactions.py` — Kaggle CSV (2 files) → 1,852,394 rows loaded ✅
  - [x] Total: **1,874,190 rows** in Snowflake RAW layer
- [ ] **Phase 3 – dbt Transformation** ← NEXT
- [ ] Phase 4 – Prefect Orchestration
- [ ] Phase 5 – Power BI Dashboards
- [ ] Phase 6 – Documentation & Polish

