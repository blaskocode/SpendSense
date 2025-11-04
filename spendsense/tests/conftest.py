"""Pytest configuration and fixtures"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path

from spendsense.storage.sqlite_manager import SQLiteManager
from spendsense.ingest.data_generator import SyntheticDataGenerator
from spendsense.ingest.importer import DataImporter
from spendsense.storage.parquet_handler import ParquetHandler


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing"""
    from pathlib import Path
    
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    db_manager = SQLiteManager()
    db_manager.db_path = Path(db_path)
    db_manager.connect()
    db_manager.create_schema()
    
    yield db_manager
    
    db_manager.close()
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def sample_user_data(temp_db):
    """Generate sample user data for testing"""
    generator = SyntheticDataGenerator(num_users=5, seed=42)
    users, accounts, transactions, liabilities = generator.generate_all()
    
    parquet_handler = ParquetHandler()
    importer = DataImporter(temp_db, parquet_handler)
    importer.import_synthetic_data(num_users=5, seed=42)
    
    return {
        'users': [u.user_id for u in users],
        'accounts': accounts,
        'transactions': transactions,
        'db_manager': temp_db
    }


@pytest.fixture
def test_user_id():
    """Return a test user ID"""
    return "test_user_001"

