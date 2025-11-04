"""Configuration management for SpendSense"""

import os
from pathlib import Path
from typing import Optional

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
NUM_USERS = int(os.getenv("NUM_USERS", "75"))  # Default 75 users (between 50-100)
SEED = int(os.getenv("SEED", "42"))  # Default seed for reproducibility

# Date settings
DAYS_OF_HISTORY = 210  # 180 days + 30 days buffer for window calculations
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

