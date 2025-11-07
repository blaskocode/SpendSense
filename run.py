#!/usr/bin/env python3
"""
SpendSense setup and run script
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from spendsense.storage.sqlite_manager import SQLiteManager
from spendsense.storage.parquet_handler import ParquetHandler
from spendsense.ingest.importer import DataImporter
from spendsense.utils.config import NUM_USERS, SEED
from spendsense.utils.logger import setup_logger

logger = setup_logger(__name__)


def setup(use_improved: bool = False, use_profiles: bool = True):
    """Setup SpendSense: create database schema and generate synthetic data"""
    logger.info("Setting up SpendSense...")
    
    # Initialize database
    db_manager = SQLiteManager()
    # Clear existing data before creating new schema
    db_manager.drop_all_tables()
    logger.info("Cleared existing database tables")
    db_manager.create_schema()
    logger.info("Database schema created")
    
    # Generate and import synthetic data
    parquet_handler = ParquetHandler()
    importer = DataImporter(db_manager, parquet_handler)
    importer.import_synthetic_data(
        num_users=NUM_USERS, 
        seed=SEED,
        use_profiles=use_profiles,
        use_improved=use_improved
    )
    
    logger.info("Setup completed successfully!")
    logger.info(f"Generated data for {NUM_USERS} users")
    logger.info(f"Database: {db_manager.db_path}")
    logger.info(f"Parquet files: {parquet_handler.parquet_dir}")


def start():
    """Start SpendSense API server"""
    import uvicorn
    from spendsense.api.main import create_app
    
    logger.info("Starting SpendSense API server...")
    app = create_app()
    
    # Start server on localhost:8000
    logger.info("Starting server on http://localhost:8000")
    logger.info("API documentation available at http://localhost:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="SpendSense setup and run script")
    parser.add_argument(
        '--setup',
        action='store_true',
        help='Setup database and generate synthetic data'
    )
    parser.add_argument(
        '--start',
        action='store_true',
        help='Start API server'
    )
    parser.add_argument(
        '--use-improved',
        action='store_true',
        help='Use improved data generator (comprehensive features)'
    )
    parser.add_argument(
        '--use-profiles',
        action='store_true',
        default=True,
        help='Use profile-based generator (realistic persona-driven data). Default: True'
    )
    parser.add_argument(
        '--no-profiles',
        action='store_true',
        help='Use Capital One synthetic-data library instead of profile-based generator'
    )
    
    args = parser.parse_args()
    
    if args.setup:
        use_profiles = not args.no_profiles if args.no_profiles else args.use_profiles
        setup(use_improved=args.use_improved, use_profiles=use_profiles)
    elif args.start:
        start()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

