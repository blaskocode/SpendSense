"""Subscription detection and analysis"""

from typing import List, Dict, Set
from datetime import date, timedelta
from collections import defaultdict
import sqlite3

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class SubscriptionDetector:
    """Detects recurring subscriptions from transaction data"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize subscription detector.
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
        self.min_recurring_count = 3  # Minimum transactions to consider recurring
        self.recurring_window_days = 90  # Days to look for recurring pattern
    
    def detect_subscriptions(
        self, 
        user_id: str, 
        transactions: List[sqlite3.Row]
    ) -> Dict[str, any]:
        """Detect subscription patterns from transactions.
        
        Args:
            user_id: User identifier
            transactions: List of transaction rows
            
        Returns:
            Dictionary with subscription metrics:
            - subscriptions_count: Number of unique recurring merchants
            - recurring_merchants: List of merchant names
            - monthly_recurring_spend: Total monthly recurring spend
            - recurring_spend_share: Share of total spend that is recurring
        """
        if not transactions:
            return {
                'subscriptions_count': 0,
                'recurring_merchants': [],
                'monthly_recurring_spend': 0.0,
                'recurring_spend_share': 0.0
            }
        
        # Group transactions by merchant
        merchant_transactions = defaultdict(list)
        total_spend = 0.0
        
        for txn in transactions:
            merchant_name = txn['merchant_name']
            if merchant_name:
                amount = abs(txn['amount'])  # Use absolute value for spend
                if txn['amount'] < 0:  # Only count negative transactions as spend
                    merchant_transactions[merchant_name].append({
                        'date': date.fromisoformat(txn['date']),
                        'amount': amount
                    })
                    total_spend += amount
        
        # Identify recurring merchants (≥3 transactions in 90 days)
        recurring_merchants = []
        recurring_monthly_spend = 0.0
        
        for merchant, txn_list in merchant_transactions.items():
            if len(txn_list) >= self.min_recurring_count:
                # Check if transactions are within 90-day window
                dates = sorted([txn['date'] for txn in txn_list])
                first_date = dates[0]
                last_date = dates[-1]
                
                if (last_date - first_date).days <= self.recurring_window_days:
                    recurring_merchants.append(merchant)
                    # Calculate average monthly spend for this merchant
                    total_merchant_spend = sum(txn['amount'] for txn in txn_list)
                    days_span = (last_date - first_date).days + 1
                    monthly_spend = (total_merchant_spend / days_span) * 30
                    recurring_monthly_spend += monthly_spend
        
        # Calculate share of total spend
        recurring_spend_share = 0.0
        if total_spend > 0:
            recurring_spend_share = (recurring_monthly_spend / (total_spend / len(transactions) * 30)) * 100
            # Cap at 100%
            recurring_spend_share = min(recurring_spend_share, 100.0)
        
        logger.debug(
            f"User {user_id}: Found {len(recurring_merchants)} recurring merchants, "
            f"${recurring_monthly_spend:.2f}/month"
        )
        
        return {
            'subscriptions_count': len(recurring_merchants),
            'recurring_merchants': recurring_merchants,
            'monthly_recurring_spend': recurring_monthly_spend,
            'recurring_spend_share': recurring_spend_share
        }

