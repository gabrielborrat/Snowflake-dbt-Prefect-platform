"""
Ingestion Configuration
-----------------------
Central configuration for all ingestion scripts.
Loads settings from environment variables (.env file).
"""

import os
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()

# --- Snowflake Connection ---
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE", "INGESTION_ROLE")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "INGESTION_WH")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "RAW")

# --- Ingestion Settings ---
LOG_LEVEL = os.getenv("INGESTION_LOG_LEVEL", "INFO")
BATCH_SIZE = int(os.getenv("INGESTION_BATCH_SIZE", "10000"))

# --- Source: Market Data ---
MARKET_TICKERS = [
    "AAPL", "MSFT",         # US Tech
    "JPM", "GS",            # US Banks
    "HSBA.L", "BNP.PA",     # EU Banks
    "SAP.DE", "NOVN.SW",    # EU Blue Chip
]

# --- Source: Exchange Rates ---
FX_BASE_CURRENCY = "EUR"
FX_TARGET_CURRENCIES = ["USD", "GBP", "CHF", "JPY", "CAD", "AUD"]
FX_API_BASE_URL = "https://api.frankfurter.app"

# --- Schemas ---
RAW_TRANSACTIONS_SCHEMA = "TRANSACTIONS"
RAW_MARKET_DATA_SCHEMA = "MARKET_DATA"
RAW_EXCHANGE_RATES_SCHEMA = "EXCHANGE_RATES"

