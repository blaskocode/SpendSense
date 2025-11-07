"""Main data import module that coordinates data generation and loading"""

import pandas as pd
from typing import List
from datetime import datetime

from .profile_generator import ProfileBasedGenerator
from .data_generator import User, Account, Transaction, Liability
# Lazy import for CapitalOneDataGenerator (only needed if use_profiles=False)
from .validator import DataValidator
from ..storage.sqlite_manager import SQLiteManager
from ..storage.parquet_handler import ParquetHandler
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class DataImporter:
    """Coordinates data generation and import into database"""
    
    def __init__(self, db_manager: SQLiteManager, parquet_handler: ParquetHandler):
        self.db_manager = db_manager
        self.parquet_handler = parquet_handler
        self.validator = DataValidator()
    
    def import_synthetic_data(self, num_users: int = None, seed: int = None, use_profiles: bool = True, use_improved: bool = False):
        """Generate and import synthetic data
        
        Args:
            num_users: Number of users to generate
            seed: Random seed for reproducibility
            use_profiles: If True, use profile-based generator (realistic). If False, use original generator.
            use_improved: If True, use improved generator (comprehensive features). Overrides use_profiles.
        """
        logger.info("Starting synthetic data import")
        
        # Generate data using improved, profile-based, or Capital One generator
        if use_improved:
            logger.info("Using improved generator with comprehensive features")
            from .improved_generator import ImprovedDataGenerator
            generator = ImprovedDataGenerator(num_users=num_users, seed=seed)
        elif use_profiles:
            logger.info("Using profile-based generator for realistic data")
            generator = ProfileBasedGenerator(num_users=num_users, seed=seed)
        else:
            logger.info("Using Capital One synthetic-data library")
            # Lazy import - only import when needed
            try:
                from .capitalone_generator import CapitalOneDataGenerator
                generator = CapitalOneDataGenerator(num_users=num_users, seed=seed)
            except ImportError:
                raise ImportError(
                    "synthetic-data package is required when use_profiles=False. "
                    "Install it with: pip install synthetic-data"
                )
        
        users, accounts, transactions, liabilities = generator.generate_all()
        
        # Validate data
        logger.info("Validating generated data")
        self.validator.validate_batch([self._user_to_dict(u) for u in users], 'user')
        self.validator.validate_batch([self._account_to_dict(a) for a in accounts], 'account')
        self.validator.validate_batch([self._transaction_to_dict(t) for t in transactions], 'transaction')
        self.validator.validate_batch([self._liability_to_dict(l) for l in liabilities], 'liability')
        
        # Import into SQLite
        logger.info("Importing data into SQLite database")
        self._import_users(users)
        self._import_accounts(accounts)
        self._import_transactions(transactions)
        self._import_liabilities(liabilities)
        
        # Export to Parquet for analytics
        logger.info("Exporting data to Parquet for analytics")
        self._export_to_parquet(accounts, transactions)
        
        logger.info("Data import completed successfully")
    
    def _import_users(self, users: List[User]):
        """Import users into database"""
        conn = self.db_manager.connect()
        cursor = conn.cursor()
        
        for user in users:
            cursor.execute("""
                INSERT OR REPLACE INTO users 
                (user_id, created_at, consent_status, consent_timestamp, last_updated)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user.user_id,
                user.created_at,
                user.consent_status,
                user.consent_timestamp,
                user.last_updated or user.created_at
            ))
        
        conn.commit()
        logger.info(f"Imported {len(users)} users")
    
    def _import_accounts(self, accounts: List[Account]):
        """Import accounts into database"""
        conn = self.db_manager.connect()
        cursor = conn.cursor()
        
        for account in accounts:
            cursor.execute("""
                INSERT OR REPLACE INTO accounts
                (account_id, user_id, type, subtype, balance_available, 
                 balance_current, balance_limit, iso_currency_code)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                account.account_id,
                account.user_id,
                account.type,
                account.subtype,
                account.balance_available,
                account.balance_current,
                account.balance_limit,
                account.iso_currency_code
            ))
        
        conn.commit()
        logger.info(f"Imported {len(accounts)} accounts")
    
    def _import_transactions(self, transactions: List[Transaction]):
        """Import transactions into database"""
        conn = self.db_manager.connect()
        cursor = conn.cursor()
        
        for transaction in transactions:
            # Convert timestamp to ISO format string if present
            timestamp_str = None
            if transaction.timestamp:
                timestamp_str = transaction.timestamp.isoformat()
            
            cursor.execute("""
                INSERT OR REPLACE INTO transactions
                (transaction_id, account_id, date, timestamp, amount, merchant_name, 
                 merchant_entity_id, payment_channel, category_primary, 
                 category_detailed, pending)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction.transaction_id,
                transaction.account_id,
                transaction.date,
                timestamp_str,
                transaction.amount,
                transaction.merchant_name,
                transaction.merchant_entity_id,
                transaction.payment_channel,
                transaction.category_primary,
                transaction.category_detailed,
                transaction.pending
            ))
        
        conn.commit()
        logger.info(f"Imported {len(transactions)} transactions")
    
    def _import_liabilities(self, liabilities: List[Liability]):
        """Import liabilities into database"""
        conn = self.db_manager.connect()
        cursor = conn.cursor()
        
        for liability in liabilities:
            cursor.execute("""
                INSERT OR REPLACE INTO liabilities
                (liability_id, account_id, type, apr, minimum_payment, 
                 last_payment, is_overdue, next_payment_due, last_statement_balance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                liability.liability_id,
                liability.account_id,
                liability.type,
                liability.apr,
                liability.minimum_payment,
                liability.last_payment,
                liability.is_overdue,
                liability.next_payment_due,
                liability.last_statement_balance
            ))
        
        conn.commit()
        logger.info(f"Imported {len(liabilities)} liabilities")
    
    def _export_to_parquet(self, accounts: List[Account], transactions: List[Transaction]):
        """Export accounts and transactions to Parquet"""
        # Convert to DataFrames
        accounts_df = pd.DataFrame([self._account_to_dict(a) for a in accounts])
        transactions_df = pd.DataFrame([self._transaction_to_dict(t) for t in transactions])
        
        # Export
        self.parquet_handler.export_accounts(accounts_df)
        self.parquet_handler.export_transactions(transactions_df)
    
    def _user_to_dict(self, user: User) -> dict:
        """Convert User dataclass to dict"""
        return {
            'user_id': user.user_id,
            'created_at': user.created_at,
            'consent_status': user.consent_status,
            'consent_timestamp': user.consent_timestamp,
            'last_updated': user.last_updated or user.created_at
        }
    
    def _account_to_dict(self, account: Account) -> dict:
        """Convert Account dataclass to dict"""
        return {
            'account_id': account.account_id,
            'user_id': account.user_id,
            'type': account.type,
            'subtype': account.subtype,
            'balance_available': account.balance_available,
            'balance_current': account.balance_current,
            'balance_limit': account.balance_limit,
            'iso_currency_code': account.iso_currency_code
        }
    
    def _transaction_to_dict(self, transaction: Transaction) -> dict:
        """Convert Transaction dataclass to dict"""
        return {
            'transaction_id': transaction.transaction_id,
            'account_id': transaction.account_id,
            'date': transaction.date,
            'amount': transaction.amount,
            'merchant_name': transaction.merchant_name,
            'merchant_entity_id': transaction.merchant_entity_id,
            'payment_channel': transaction.payment_channel,
            'category_primary': transaction.category_primary,
            'category_detailed': transaction.category_detailed,
            'pending': transaction.pending
        }
    
    def _liability_to_dict(self, liability: Liability) -> dict:
        """Convert Liability dataclass to dict"""
        return {
            'liability_id': liability.liability_id,
            'account_id': liability.account_id,
            'type': liability.type,
            'apr': liability.apr,
            'minimum_payment': liability.minimum_payment,
            'last_payment': liability.last_payment,
            'is_overdue': liability.is_overdue,
            'next_payment_due': liability.next_payment_due,
            'last_statement_balance': liability.last_statement_balance
        }

