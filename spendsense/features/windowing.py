"""Time window partitioning for transaction analysis"""

from datetime import date, timedelta
from typing import List, Tuple, Optional
import sqlite3

from ..utils.config import TODAY
from ..utils.logger import setup_logger
from ..utils.errors import DataError

logger = setup_logger(__name__)


class TimeWindowPartitioner:
    """Partitions transactions into rolling time windows"""
    
    def __init__(self, db_connection: sqlite3.Connection, reference_date: Optional[date] = None):
        """Initialize window partitioner.
        
        Args:
            db_connection: SQLite database connection
            reference_date: Reference date for window calculations (defaults to TODAY)
        """
        self.conn = db_connection
        self.reference_date = reference_date or TODAY
    
    def get_30_day_window(self) -> Tuple[date, date]:
        """Get 30-day rolling window boundaries.
        
        Returns:
            Tuple of (start_date, end_date) for 30-day window
            Window: [today-30, today-1] (excludes today)
        """
        end_date = self.reference_date - timedelta(days=1)
        start_date = end_date - timedelta(days=29)  # 30 days total (inclusive)
        return start_date, end_date
    
    def get_180_day_window(self) -> Tuple[date, date]:
        """Get 180-day rolling window boundaries.
        
        Returns:
            Tuple of (start_date, end_date) for 180-day window
            Window: [today-180, today-1] (excludes today)
        """
        end_date = self.reference_date - timedelta(days=1)
        start_date = end_date - timedelta(days=179)  # 180 days total (inclusive)
        return start_date, end_date
    
    def get_transactions_in_window(
        self, 
        user_id: str, 
        window_type: str,
        exclude_pending: bool = True
    ) -> List[sqlite3.Row]:
        """Get all transactions for a user within a specified window.
        
        Args:
            user_id: User identifier
            window_type: '30d' or '180d'
            exclude_pending: If True, exclude pending transactions
            
        Returns:
            List of transaction rows matching the criteria
            
        Raises:
            DataError: If window_type is invalid
        """
        if window_type == '30d':
            start_date, end_date = self.get_30_day_window()
        elif window_type == '180d':
            start_date, end_date = self.get_180_day_window()
        else:
            raise DataError(f"Invalid window_type: {window_type}. Must be '30d' or '180d'")
        
        cursor = self.conn.cursor()
        
        # Build query with optional pending exclusion
        query = """
            SELECT t.*
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.user_id = ?
              AND t.date >= ?
              AND t.date <= ?
        """
        
        params = [user_id, start_date, end_date]
        
        if exclude_pending:
            query += " AND t.pending = 0"
        
        query += " ORDER BY t.date ASC"
        
        cursor.execute(query, params)
        transactions = cursor.fetchall()
        
        logger.debug(
            f"Found {len(transactions)} transactions for user {user_id} "
            f"in {window_type} window ({start_date} to {end_date})"
        )
        
        return transactions
    
    def get_user_data_span(self, user_id: str) -> Tuple[Optional[date], Optional[date], int]:
        """Get the date range and total days of data for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Tuple of (earliest_date, latest_date, total_days)
            Returns (None, None, 0) if user has no transactions
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT MIN(t.date) as earliest, MAX(t.date) as latest
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.user_id = ? AND t.pending = 0
        """, (user_id,))
        
        result = cursor.fetchone()
        
        if result and result['earliest'] and result['latest']:
            earliest = date.fromisoformat(result['earliest'])
            latest = date.fromisoformat(result['latest'])
            total_days = (latest - earliest).days + 1
            return earliest, latest, total_days
        
        return None, None, 0
    
    def get_user_data_age(self, user_id: str) -> int:
        """Get the number of days of data available for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of days between earliest transaction and reference_date
            Returns 0 if user has no transactions
        """
        earliest, _, _ = self.get_user_data_span(user_id)
        
        if earliest:
            return (self.reference_date - earliest).days
        
        return 0
    
    def classify_user_data_availability(self, user_id: str) -> str:
        """Classify user's data availability for graceful degradation.
        
        Args:
            user_id: User identifier
            
        Returns:
            One of: 'new' (<7 days), 'limited' (7-29 days), 'full_30' (30+ days), 'full_180' (180+ days)
        """
        days_available = self.get_user_data_age(user_id)
        
        if days_available < 7:
            return 'new'
        elif days_available < 30:
            return 'limited'
        elif days_available < 180:
            return 'full_30'
        else:
            return 'full_180'

