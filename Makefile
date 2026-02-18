# =============================================================================
# Snowflake Modern Data Stack Portfolio - Makefile
# =============================================================================
# Usage: make <target>
# =============================================================================

.PHONY: help setup install venv dbt-deps dbt-run dbt-test dbt-docs dbt-fresh \
        ingest-all ingest-transactions ingest-market ingest-fx \
        prefect-server prefect-run test clean

# --- Default ---
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

# --- Setup ---
venv: ## Create Python virtual environment
	python3 -m venv venv
	@echo "Activate with: source venv/bin/activate"

install: ## Install Python dependencies
	pip install -r requirements.txt

setup: venv ## Full setup: venv + install + dbt deps
	. venv/bin/activate && pip install -r requirements.txt
	. venv/bin/activate && cd dbt_project && dbt deps

# --- dbt ---
dbt-deps: ## Install dbt packages
	cd dbt_project && dbt deps

dbt-run: ## Run all dbt models
	cd dbt_project && dbt run

dbt-test: ## Run all dbt tests
	cd dbt_project && dbt test

dbt-docs: ## Generate and serve dbt documentation
	cd dbt_project && dbt docs generate && dbt docs serve

dbt-fresh: ## Check source freshness
	cd dbt_project && dbt source freshness

dbt-build: ## Run dbt build (run + test)
	cd dbt_project && dbt build

# --- Ingestion ---
ingest-all: ## Run all ingestion scripts
	python -m ingestion.sources.ingest_transactions
	python -m ingestion.sources.ingest_market_prices
	python -m ingestion.sources.ingest_exchange_rates

ingest-transactions: ## Ingest credit card transactions (CSV)
	python -m ingestion.sources.ingest_transactions

ingest-market: ## Ingest market prices (yfinance API)
	python -m ingestion.sources.ingest_market_prices

ingest-fx: ## Ingest exchange rates (frankfurter.app API)
	python -m ingestion.sources.ingest_exchange_rates

# --- Prefect ---
prefect-server: ## Start Prefect local server
	prefect server start

prefect-run: ## Run the full pipeline flow
	python -m orchestration.flows.full_pipeline_flow

# --- Testing ---
test: ## Run Python tests
	pytest ingestion/tests/ -v

# --- Cleanup ---
clean: ## Clean generated files
	rm -rf dbt_project/target/
	rm -rf dbt_project/dbt_packages/
	rm -rf dbt_project/logs/
	rm -rf __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned."

