"""Credit utilization and analysis"""

from typing import List, Dict
import sqlite3

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class CreditDetector:
    """Detects credit utilization and payment patterns"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize credit detector.
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
    
    def detect_credit_signals(
        self,
        user_id: str
    ) -> Dict[str, any]:
        """Detect credit-related signals.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with credit metrics:
            - credit_utilization: Highest utilization percentage across cards
            - utilization_30_flag: True if any card ≥30%
            - utilization_50_flag: True if any card ≥50%
            - utilization_80_flag: True if any card ≥80%
            - min_payment_only: True if only making minimum payments
            - interest_charges: Total monthly interest charges
            - is_overdue: True if any card is overdue
        """
        cursor = self.conn.cursor()
        
        # Get all credit card accounts with liabilities
        cursor.execute("""
            SELECT 
                a.account_id,
                a.balance_current,
                a.balance_limit,
                l.apr,
                l.minimum_payment,
                l.is_overdue,
                l.last_statement_balance
            FROM accounts a
            LEFT JOIN liabilities l ON a.account_id = l.account_id
            WHERE a.user_id = ? AND a.type = 'credit'
        """, (user_id,))
        
        credit_accounts = cursor.fetchall()
        
        if not credit_accounts:
            return {
                'credit_utilization': 0.0,
                'utilization_30_flag': False,
                'utilization_50_flag': False,
                'utilization_80_flag': False,
                'min_payment_only': False,
                'interest_charges': 0.0,
                'is_overdue': False
            }
        
        # Calculate utilization for each card
        max_utilization = 0.0
        total_interest = 0.0
        is_overdue = False
        min_payment_only = True
        
        for account in credit_accounts:
            balance = account['balance_current'] or 0.0
            limit = account['balance_limit'] or 0.0
            
            if limit > 0:
                utilization = (balance / limit) * 100
                max_utilization = max(max_utilization, utilization)
            
            # Check overdue status
            if account['is_overdue']:
                is_overdue = True
            
            # Calculate interest charges (simplified: APR * balance / 12)
            if account['apr'] and balance > 0:
                monthly_interest = (account['apr'] / 100) * balance / 12
                total_interest += monthly_interest
            
            # Check if making minimum payment only
            # This is detected by checking if payment amount ≈ minimum payment
            # We'll need to check actual payments in transactions
            # For now, assume min_payment_only if we can't determine otherwise
        
        # Check payment patterns from transactions
        cursor.execute("""
            SELECT SUM(ABS(amount)) as total_payments
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.user_id = ? 
              AND a.type = 'credit'
              AND t.amount > 0
              AND t.merchant_name LIKE '%Payment%'
        """, (user_id,))
        
        payment_result = cursor.fetchone()
        total_payments = payment_result['total_payments'] or 0.0
        
        # Compare payments to minimum payments
        total_minimum = sum(
            acc['minimum_payment'] or 0.0 
            for acc in credit_accounts 
            if acc['minimum_payment']
        )
        
        if total_minimum > 0 and total_payments > total_minimum * 1.1:
            min_payment_only = False
        
        logger.debug(
            f"User {user_id}: Credit - {max_utilization:.1f}% utilization, "
            f"${total_interest:.2f}/month interest, overdue: {is_overdue}"
        )
        
        return {
            'credit_utilization': max_utilization,
            'utilization_30_flag': max_utilization >= 30.0,
            'utilization_50_flag': max_utilization >= 50.0,
            'utilization_80_flag': max_utilization >= 80.0,
            'min_payment_only': min_payment_only,
            'interest_charges': total_interest,
            'is_overdue': is_overdue
        }

