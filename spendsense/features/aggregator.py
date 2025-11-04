"""Signal aggregation and orchestration"""

from typing import Dict, Optional
from datetime import datetime
import sqlite3

from .windowing import TimeWindowPartitioner
from .subscriptions import SubscriptionDetector
from .savings import SavingsDetector
from .credit import CreditDetector
from .income import IncomeDetector
from ..utils.logger import setup_logger
from ..utils.errors import DataError

logger = setup_logger(__name__)


class SignalAggregator:
    """Aggregates all behavioral signals for a user"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize signal aggregator.
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
        self.windower = TimeWindowPartitioner(db_connection)
        self.subscription_detector = SubscriptionDetector(db_connection)
        self.savings_detector = SavingsDetector(db_connection)
        self.credit_detector = CreditDetector(db_connection)
        self.income_detector = IncomeDetector(db_connection)
    
    def compute_signals(
        self,
        user_id: str,
        window_type: str = '30d',
        use_cache: bool = True
    ) -> Dict[str, any]:
        """Compute all behavioral signals for a user.
        
        Args:
            user_id: User identifier
            window_type: '30d' or '180d'
            use_cache: If True, check cache before computing
            
        Returns:
            Dictionary containing all aggregated signals
        """
        if window_type not in ['30d', '180d']:
            raise DataError(f"Invalid window_type: {window_type}. Must be '30d' or '180d'")
        
        # Check cache if enabled
        if use_cache:
            cached = self._get_cached_signals(user_id, window_type)
            if cached:
                logger.debug(f"Using cached signals for user {user_id}, window {window_type}")
                return cached
        
        # Get transactions for the window
        transactions = self.windower.get_transactions_in_window(
            user_id, 
            window_type, 
            exclude_pending=True
        )
        
        # Calculate window days
        window_days = 30 if window_type == '30d' else 180
        
        # Compute all signals
        subscription_signals = self.subscription_detector.detect_subscriptions(
            user_id, transactions
        )
        
        savings_signals = self.savings_detector.detect_savings_signals(
            user_id, transactions, window_days
        )
        
        credit_signals = self.credit_detector.detect_credit_signals(user_id)
        
        income_signals = self.income_detector.detect_income_signals(
            user_id, transactions, window_days
        )
        
        # Aggregate all signals
        aggregated = {
            'user_id': user_id,
            'window_type': window_type,
            'computed_at': datetime.now().isoformat(),
            'subscriptions': subscription_signals,
            'savings': savings_signals,
            'credit': credit_signals,
            'income': income_signals
        }
        
        # Cache the results
        if use_cache:
            self._cache_signals(aggregated)
        
        logger.info(
            f"Computed signals for user {user_id}, window {window_type}: "
            f"{subscription_signals['subscriptions_count']} subscriptions, "
            f"{credit_signals['credit_utilization']:.1f}% utilization"
        )
        
        return aggregated
    
    def get_user_data_availability(self, user_id: str) -> str:
        """Get user's data availability classification.
        
        Args:
            user_id: User identifier
            
        Returns:
            Classification: 'new', 'limited', 'full_30', or 'full_180'
        """
        return self.windower.classify_user_data_availability(user_id)
    
    def _get_cached_signals(
        self, 
        user_id: str, 
        window_type: str
    ) -> Optional[Dict[str, any]]:
        """Retrieve cached signals if available and fresh.
        
        Args:
            user_id: User identifier
            window_type: '30d' or '180d'
            
        Returns:
            Cached signals dictionary or None if not available/fresh
        """
        cursor = self.conn.cursor()
        
        # Check for cached signals within last 24 hours
        cursor.execute("""
            SELECT computed_at, subscriptions_count, recurring_spend, 
                   savings_growth_rate, credit_utilization, income_buffer_months
            FROM signals
            WHERE user_id = ? AND window_type = ?
              AND datetime(computed_at) > datetime('now', '-24 hours')
            ORDER BY computed_at DESC
            LIMIT 1
        """, (user_id, window_type))
        
        result = cursor.fetchone()
        
        if result:
            # Reconstruct signals dict from cached data
            # Note: This is a simplified version - full cache would store all fields
            return {
                'user_id': user_id,
                'window_type': window_type,
                'computed_at': result['computed_at'],
                'subscriptions': {
                    'subscriptions_count': result['subscriptions_count'] or 0,
                    'monthly_recurring_spend': result['recurring_spend'] or 0.0
                },
                'credit': {
                    'credit_utilization': result['credit_utilization'] or 0.0
                },
                'savings': {
                    'savings_growth_rate': result['savings_growth_rate'] or 0.0
                },
                'income': {
                    'cash_flow_buffer_months': result['income_buffer_months'] or 0.0
                }
            }
        
        return None
    
    def _cache_signals(self, signals: Dict[str, any]):
        """Cache computed signals in database.
        
        Args:
            signals: Aggregated signals dictionary
        """
        cursor = self.conn.cursor()
        
        signal_id = f"{signals['user_id']}_{signals['window_type']}_{signals['computed_at']}"
        
        # Extract key metrics for caching
        subscriptions = signals.get('subscriptions', {})
        savings = signals.get('savings', {})
        credit = signals.get('credit', {})
        income = signals.get('income', {})
        
        cursor.execute("""
            INSERT OR REPLACE INTO signals (
                signal_id, user_id, window_type, computed_at,
                subscriptions_count, recurring_spend,
                savings_growth_rate, credit_utilization, income_buffer_months
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            signal_id,
            signals['user_id'],
            signals['window_type'],
            signals['computed_at'],
            subscriptions.get('subscriptions_count', 0),
            subscriptions.get('monthly_recurring_spend', 0.0),
            savings.get('savings_growth_rate', 0.0),
            credit.get('credit_utilization', 0.0),
            income.get('cash_flow_buffer_months', 0.0)
        ))
        
        self.conn.commit()
        logger.debug(f"Cached signals for user {signals['user_id']}, window {signals['window_type']}")

