"""Income stability detection and analysis"""

from typing import List, Dict, Optional
from datetime import date, timedelta
from collections import defaultdict
import sqlite3

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class IncomeDetector:
    """Detects income stability and cash flow patterns"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize income detector.
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
    
    def detect_income_signals(
        self,
        user_id: str,
        transactions: List[sqlite3.Row],
        window_days: int
    ) -> Dict[str, any]:
        """Detect income-related signals from transactions.
        
        Args:
            user_id: User identifier
            transactions: List of transaction rows
            window_days: Number of days in the analysis window
            
        Returns:
            Dictionary with income metrics:
            - payroll_frequency: 'monthly', 'semi_monthly', 'biweekly', or 'unknown'
            - median_pay_gap_days: Median days between payroll deposits
            - income_variability: Coefficient of variation in payroll amounts
            - monthly_income: Estimated monthly income
            - cash_flow_buffer_months: Months of expenses covered by checking balance
        """
        if not transactions:
            return {
                'payroll_frequency': 'unknown',
                'median_pay_gap_days': 0,
                'income_variability': 0.0,
                'monthly_income': 0.0,
                'cash_flow_buffer_months': 0.0
            }
        
        # Detect payroll deposits (positive ACH transactions or large regular deposits)
        payroll_deposits = []
        for txn in transactions:
            amount = txn['amount']
            merchant_name = (txn['merchant_name'] or '').lower()
            payment_channel = txn['payment_channel'] or ''
            
            # Look for payroll indicators
            is_payroll = (
                amount > 0 and (
                    payment_channel == 'ach' or
                    'payroll' in merchant_name or
                    'deposit' in merchant_name or
                    # Large regular deposits (likely payroll) - threshold: $500+
                    (amount >= 500 and payment_channel in ('ach', 'other'))
                )
            )
            
            if is_payroll:
                payroll_deposits.append({
                    'date': date.fromisoformat(txn['date']),
                    'amount': amount
                })
        
        if not payroll_deposits:
            return {
                'payroll_frequency': 'unknown',
                'median_pay_gap_days': 0,
                'income_variability': 0.0,
                'monthly_income': 0.0,
                'cash_flow_buffer_months': 0.0
            }
        
        # Sort by date
        payroll_deposits.sort(key=lambda x: x['date'])
        
        # Calculate gaps between deposits
        gaps = []
        amounts = []
        
        for i in range(1, len(payroll_deposits)):
            gap = (payroll_deposits[i]['date'] - payroll_deposits[i-1]['date']).days
            gaps.append(gap)
            amounts.append(payroll_deposits[i]['amount'])
        
        # Add first amount
        if payroll_deposits:
            amounts.append(payroll_deposits[0]['amount'])
        
        # Calculate median gap
        median_gap = 0
        if gaps:
            sorted_gaps = sorted(gaps)
            mid = len(sorted_gaps) // 2
            median_gap = sorted_gaps[mid] if len(sorted_gaps) % 2 == 1 else (sorted_gaps[mid-1] + sorted_gaps[mid]) / 2
        
        # Determine frequency
        if median_gap >= 25:
            frequency = 'monthly'
        elif median_gap >= 13:
            frequency = 'semi_monthly'
        elif median_gap >= 12:
            frequency = 'biweekly'
        else:
            frequency = 'unknown'
        
        # Calculate income variability (coefficient of variation)
        if amounts:
            mean_amount = sum(amounts) / len(amounts)
            if mean_amount > 0:
                variance = sum((a - mean_amount) ** 2 for a in amounts) / len(amounts)
                std_dev = variance ** 0.5
                income_variability = (std_dev / mean_amount) * 100
            else:
                income_variability = 0.0
        else:
            income_variability = 0.0
        
        # Calculate monthly income
        total_income = sum(amounts)
        monthly_income = 0.0
        if window_days > 0:
            monthly_income = (total_income / window_days) * 30
        
        # Calculate cash flow buffer
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT SUM(balance_current) as total_checking
            FROM accounts
            WHERE user_id = ? AND type = 'depository' AND subtype = 'checking'
        """, (user_id,))
        
        result = cursor.fetchone()
        checking_balance = result['total_checking'] or 0.0
        
        # Estimate monthly expenses
        total_expenses = abs(sum(txn['amount'] for txn in transactions if txn['amount'] < 0))
        monthly_expenses = (total_expenses / window_days) * 30 if window_days > 0 else 0.0
        
        cash_flow_buffer_months = 0.0
        if monthly_expenses > 0:
            cash_flow_buffer_months = checking_balance / monthly_expenses
        
        logger.debug(
            f"User {user_id}: Income - {frequency} frequency, "
            f"${monthly_income:.2f}/month, {cash_flow_buffer_months:.1f} months buffer"
        )
        
        return {
            'payroll_frequency': frequency,
            'median_pay_gap_days': int(median_gap),
            'income_variability': income_variability,
            'monthly_income': monthly_income,
            'cash_flow_buffer_months': cash_flow_buffer_months
        }

