"""Savings signal detection and analysis"""

from typing import List, Dict
from datetime import date
import sqlite3

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class SavingsDetector:
    """Detects savings patterns and growth"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize savings detector.
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
    
    def detect_savings_signals(
        self,
        user_id: str,
        transactions: List[sqlite3.Row],
        window_days: int
    ) -> Dict[str, any]:
        """Detect savings-related signals from transactions.
        
        Args:
            user_id: User identifier
            transactions: List of transaction rows
            window_days: Number of days in the analysis window
            
        Returns:
            Dictionary with savings metrics:
            - net_savings_inflow: Net positive flow to savings accounts
            - savings_growth_rate: Percentage growth rate
            - emergency_fund_months: Estimated months of expenses covered
        """
        if not transactions:
            return {
                'net_savings_inflow': 0.0,
                'savings_growth_rate': 0.0,
                'emergency_fund_months': 0.0
            }
        
        # Get savings accounts for this user
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT account_id, balance_current, balance_available
            FROM accounts
            WHERE user_id = ? AND type = 'depository' 
              AND subtype IN ('savings', 'money_market')
        """, (user_id,))
        
        savings_accounts = cursor.fetchall()
        
        # Calculate net inflow to savings accounts
        net_inflow = 0.0
        savings_account_ids = {acc['account_id'] for acc in savings_accounts}
        
        for txn in transactions:
            if txn['account_id'] in savings_account_ids:
                # Positive amounts are inflows (deposits)
                if txn['amount'] > 0:
                    net_inflow += txn['amount']
                # Negative amounts are outflows (withdrawals)
                else:
                    net_inflow += txn['amount']  # Already negative
        
        # Calculate monthly inflow
        monthly_inflow = (net_inflow / window_days) * 30 if window_days > 0 else 0.0
        
        # Get current savings balance
        current_savings = sum(acc['balance_current'] or 0.0 for acc in savings_accounts)
        
        # Calculate growth rate (only if we have a starting balance)
        growth_rate = 0.0
        if current_savings > 0 and window_days >= 30:
            # Estimate starting balance (current - net_inflow)
            estimated_start_balance = current_savings - net_inflow
            if estimated_start_balance > 0:
                growth_rate = (net_inflow / estimated_start_balance) * 100
        
        # Calculate emergency fund coverage
        # Estimate monthly expenses from total negative transactions
        total_expenses = abs(sum(txn['amount'] for txn in transactions if txn['amount'] < 0))
        monthly_expenses = (total_expenses / window_days) * 30 if window_days > 0 else 0.0
        
        emergency_fund_months = 0.0
        if monthly_expenses > 0:
            emergency_fund_months = current_savings / monthly_expenses
        
        logger.debug(
            f"User {user_id}: Savings - ${monthly_inflow:.2f}/month inflow, "
            f"{growth_rate:.2f}% growth, {emergency_fund_months:.1f} months coverage"
        )
        
        return {
            'net_savings_inflow': monthly_inflow,
            'savings_growth_rate': growth_rate,
            'emergency_fund_months': emergency_fund_months
        }

