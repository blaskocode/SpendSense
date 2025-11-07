"""Configuration management for SpendSense"""

import os
from pathlib import Path
from typing import Optional

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Load .env file from project root
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    # python-dotenv not installed, skip .env loading
    # Users can still set environment variables manually
    pass

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Database paths
DB_DIR = PROJECT_ROOT / "data"
DB_PATH = DB_DIR / "spendsense.db"
PARQUET_DIR = DB_DIR / "parquet"

# Ensure directories exist
DB_DIR.mkdir(exist_ok=True)
PARQUET_DIR.mkdir(exist_ok=True)

# Data generation settings
NUM_USERS = int(os.getenv("NUM_USERS", "100"))  # Default 100 users
SEED = int(os.getenv("SEED", "42"))  # Default seed for reproducibility

# Date settings
DAYS_OF_HISTORY = int(os.getenv("DAYS_OF_HISTORY", "365"))  # Full year of transaction history (365 days)
TODAY = None  # Will be set to current date or test date

def set_today(date: Optional[str] = None):
    """Set the 'today' date for calculations (useful for testing)"""
    global TODAY
    if date:
        from datetime import datetime
        TODAY = datetime.strptime(date, "%Y-%m-%d").date()
    else:
        from datetime import date
        TODAY = date.today()

# Initialize TODAY
if TODAY is None:
    set_today()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# Model selection:
#   - gpt-4o-mini (RECOMMENDED): Fastest, cheapest, 60% cheaper than GPT-3.5-turbo, great for structured tasks
#   - gpt-3.5-turbo: Good alternative, slightly more expensive but still cost-effective
#   - gpt-4o: More capable, 10x more expensive, use only if you need advanced reasoning
#   - gpt-4: Most capable, most expensive, use for complex analysis
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Default to GPT-4o-mini (best price/performance)
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "4000"))  # Max tokens for completion
OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "30"))  # Request timeout in seconds
# Temperature: 0.0-2.0, lower = more consistent/factual, higher = more creative
# For financial advice, lower temperature (0.3-0.4) provides more consistent, factual recommendations
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))  # Lower for financial recommendations

