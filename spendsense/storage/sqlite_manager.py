"""SQLite database manager for SpendSense"""

import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime

from ..utils.config import DB_PATH
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class SQLiteManager:
    """Manages SQLite database connections and schema"""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.conn: Optional[sqlite3.Connection] = None
        
    def connect(self) -> sqlite3.Connection:
        """Create or connect to database"""
        if self.conn is None:
            # Ensure parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row  # Enable column access by name
            logger.info(f"Connected to database: {self.db_path}")
        return self.conn
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Database connection closed")
    
    def create_schema(self):
        """Create all database tables"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    created_at TIMESTAMP NOT NULL,
                    consent_status BOOLEAN DEFAULT FALSE,
                    consent_timestamp TIMESTAMP,
                    last_updated TIMESTAMP NOT NULL
                )
            """)
            
            # Accounts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    account_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    subtype TEXT,
                    balance_available REAL,
                    balance_current REAL,
                    balance_limit REAL,
                    iso_currency_code TEXT DEFAULT 'USD',
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    date DATE NOT NULL,
                    amount REAL NOT NULL,
                    merchant_name TEXT,
                    merchant_entity_id TEXT,
                    payment_channel TEXT,
                    category_primary TEXT,
                    category_detailed TEXT,
                    pending BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
                )
            """)
            
            # Liabilities table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS liabilities (
                    liability_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    apr REAL,
                    minimum_payment REAL,
                    last_payment REAL,
                    is_overdue BOOLEAN DEFAULT FALSE,
                    next_payment_due DATE,
                    last_statement_balance REAL,
                    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
                )
            """)
            
            # Signals table (cache)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    signal_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    window_type TEXT NOT NULL,
                    computed_at TIMESTAMP NOT NULL,
                    subscriptions_count INTEGER DEFAULT 0,
                    recurring_spend REAL DEFAULT 0,
                    savings_growth_rate REAL DEFAULT 0,
                    credit_utilization REAL DEFAULT 0,
                    income_buffer_months REAL DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Personas table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS personas (
                    assignment_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    persona_name TEXT NOT NULL,
                    assigned_at TIMESTAMP NOT NULL,
                    priority_level INTEGER NOT NULL,
                    signal_strength REAL DEFAULT 0,
                    decision_trace TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Recommendations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recommendations (
                    recommendation_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    persona_name TEXT,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    generated_at TIMESTAMP NOT NULL,
                    operator_status TEXT DEFAULT 'pending',
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    feedback_id TEXT PRIMARY KEY,
                    recommendation_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    thumbs_up BOOLEAN,
                    helped_me BOOLEAN,
                    applied_this BOOLEAN,
                    free_text TEXT,
                    submitted_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(account_id, date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_user ON accounts(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_user_window ON signals(user_id, window_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_personas_user ON personas(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_recommendations_user ON recommendations(user_id)")
            
            conn.commit()
            logger.info("Database schema created successfully")
            
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Error creating schema: {e}")
            raise
    
    def drop_all_tables(self):
        """Drop all tables (for testing/reset)"""
        conn = self.connect()
        cursor = conn.cursor()
        
        tables = [
            'feedback', 'recommendations', 'personas', 'signals',
            'liabilities', 'transactions', 'accounts', 'users'
        ]
        
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        
        conn.commit()
        logger.info("All tables dropped")
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

