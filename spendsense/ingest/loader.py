"""Data loader for importing CSV/JSON data into SpendSense"""

import csv
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from ..storage.sqlite_manager import SQLiteManager
from ..utils.logger import setup_logger
from ..utils.errors import ValidationError

logger = setup_logger(__name__)


class DataLoader:
    """Loads data from CSV/JSON files into database"""
    
    def __init__(self, db_manager: SQLiteManager):
        self.db_manager = db_manager
    
    def load_from_csv(self, filepath: Path, table_name: str):
        """Load data from CSV file into database table"""
        logger.info(f"Loading CSV file: {filepath} into table: {table_name}")
        
        if not filepath.exists():
            raise FileNotFoundError(f"CSV file not found: {filepath}")
        
        df = pd.read_csv(filepath)
        conn = self.db_manager.connect()
        
        try:
            df.to_sql(table_name, conn, if_exists='append', index=False)
            logger.info(f"Loaded {len(df)} rows into {table_name}")
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            raise
    
    def load_from_json(self, filepath: Path, table_name: str):
        """Load data from JSON file into database table"""
        logger.info(f"Loading JSON file: {filepath} into table: {table_name}")
        
        if not filepath.exists():
            raise FileNotFoundError(f"JSON file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise ValidationError("JSON file must contain an array of objects")
        
        df = pd.DataFrame(data)
        conn = self.db_manager.connect()
        
        try:
            df.to_sql(table_name, conn, if_exists='append', index=False)
            logger.info(f"Loaded {len(df)} rows into {table_name}")
        except Exception as e:
            logger.error(f"Error loading JSON: {e}")
            raise
    
    def export_to_csv(self, table_name: str, output_path: Path):
        """Export database table to CSV"""
        logger.info(f"Exporting table {table_name} to CSV: {output_path}")
        
        conn = self.db_manager.connect()
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        df.to_csv(output_path, index=False)
        logger.info(f"Exported {len(df)} rows to {output_path}")
    
    def export_to_json(self, table_name: str, output_path: Path):
        """Export database table to JSON"""
        logger.info(f"Exporting table {table_name} to JSON: {output_path}")
        
        conn = self.db_manager.connect()
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        df.to_json(output_path, orient='records', date_format='iso')
        logger.info(f"Exported {len(df)} rows to {output_path}")

