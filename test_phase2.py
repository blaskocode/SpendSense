#!/usr/bin/env python3
"""Test script for Phase 2: Feature Engineering"""

import sqlite3
from spendsense.storage.sqlite_manager import SQLiteManager
from spendsense.features.aggregator import SignalAggregator
from spendsense.features.degradation import GracefulDegradation
from spendsense.utils.config import DB_PATH

def test_phase2():
    """Test Phase 2 feature engineering"""
    print("Testing Phase 2: Feature Engineering\n")
    
    # Connect to database
    db_manager = SQLiteManager()
    db_manager.connect()
    
    try:
        aggregator = SignalAggregator(db_manager.conn)
        degradation = GracefulDegradation(aggregator)
        
        # Test with a few sample users
        cursor = db_manager.conn.cursor()
        cursor.execute("SELECT user_id FROM users LIMIT 5")
        test_users = [row['user_id'] for row in cursor.fetchall()]
        
        print(f"Testing with {len(test_users)} users:\n")
        
        for user_id in test_users:
            print(f"\n{'='*60}")
            print(f"User: {user_id}")
            print(f"{'='*60}")
            
            # Get degradation info
            degradation_result = degradation.get_signals_with_degradation(user_id)
            print(f"Data Availability: {degradation_result['data_availability']}")
            print(f"Can compute 30d: {degradation_result['can_compute_30d']}")
            print(f"Can compute 180d: {degradation_result['can_compute_180d']}")
            
            if degradation_result['disclaimer']:
                print(f"Disclaimer: {degradation_result['disclaimer']}")
            
            # Get primary signals
            signals = degradation.get_primary_signals(user_id)
            
            if signals.get('subscriptions'):
                sub = signals['subscriptions']
                print(f"\nSubscriptions:")
                print(f"  Count: {sub.get('subscriptions_count', 0)}")
                print(f"  Monthly Spend: ${sub.get('monthly_recurring_spend', 0.0):.2f}")
            
            if signals.get('credit'):
                credit = signals['credit']
                print(f"\nCredit:")
                print(f"  Utilization: {credit.get('credit_utilization', 0.0):.1f}%")
                print(f"  Interest Charges: ${credit.get('interest_charges', 0.0):.2f}/month")
                print(f"  Overdue: {credit.get('is_overdue', False)}")
            
            if signals.get('savings'):
                savings = signals['savings']
                print(f"\nSavings:")
                print(f"  Growth Rate: {savings.get('savings_growth_rate', 0.0):.2f}%")
                print(f"  Monthly Inflow: ${savings.get('net_savings_inflow', 0.0):.2f}")
                print(f"  Emergency Fund: {savings.get('emergency_fund_months', 0.0):.1f} months")
            
            if signals.get('income'):
                income = signals['income']
                print(f"\nIncome:")
                print(f"  Frequency: {income.get('payroll_frequency', 'unknown')}")
                print(f"  Monthly Income: ${income.get('monthly_income', 0.0):.2f}")
                print(f"  Cash Buffer: {income.get('cash_flow_buffer_months', 0.0):.1f} months")
        
        print(f"\n{'='*60}")
        print("Phase 2 Test Complete!")
        print(f"{'='*60}\n")
        
    finally:
        db_manager.close()

if __name__ == '__main__':
    test_phase2()

