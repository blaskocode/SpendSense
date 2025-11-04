"""Parquet storage handler for analytics"""

import pandas as pd
from pathlib import Path
from typing import Optional
from datetime import datetime

from ..utils.config import PARQUET_DIR
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ParquetHandler:
    """Handles Parquet file storage for analytics"""
    
    def __init__(self, parquet_dir: Optional[Path] = None):
        self.parquet_dir = parquet_dir or PARQUET_DIR
        self.parquet_dir.mkdir(parents=True, exist_ok=True)
    
    def save_dataframe(self, df: pd.DataFrame, filename: str):
        """Save DataFrame to Parquet file"""
        filepath = self.parquet_dir / f"{filename}.parquet"
        df.to_parquet(filepath, index=False)
        logger.info(f"Saved DataFrame to {filepath}")
    
    def load_dataframe(self, filename: str) -> pd.DataFrame:
        """Load DataFrame from Parquet file"""
        filepath = self.parquet_dir / f"{filename}.parquet"
        if not filepath.exists():
            raise FileNotFoundError(f"Parquet file not found: {filepath}")
        df = pd.read_parquet(filepath)
        logger.info(f"Loaded DataFrame from {filepath}")
        return df
    
    def export_transactions(self, transactions_df: pd.DataFrame):
        """Export transactions to Parquet for analytics"""
        self.save_dataframe(transactions_df, "transactions")
    
    def export_accounts(self, accounts_df: pd.DataFrame):
        """Export accounts to Parquet for analytics"""
        self.save_dataframe(accounts_df, "accounts")
    
    def export_signals(self, signals_df: pd.DataFrame):
        """Export signals to Parquet for analytics"""
        self.save_dataframe(signals_df, "signals")

