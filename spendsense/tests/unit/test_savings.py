"""Unit tests for savings signal detection"""

import pytest
from datetime import datetime, timedelta
from spendsense.features.savings import SavingsDetector


def test_savings_growth_rate_calculation(temp_db):
    """Test savings growth rate calculation"""
    detector = SavingsDetector(temp_db.conn)
    
    # Create test user and savings account
    cursor = temp_db.conn.cursor()
    cursor.execute("INSERT INTO users (user_id, created_at, last_updated) VALUES (?, ?, ?)",
                   ("test_savings", datetime.now(), datetime.now()))
    
    cursor.execute("""
        INSERT INTO accounts (account_id, user_id, type, balance_current)
        VALUES (?, ?, ?, ?)
    """, ("acc_savings", "test_savings", "savings", 1000.0))
    
    # Create transactions showing growth
    base_date = datetime.now() - timedelta(days=30)
    transactions = []
    
    # Starting balance: $1000, add $200/month
    for i in range(6):
        transactions.append({
            'transaction_id': f"txn_{i}",
            'account_id': 'acc_savings',
            'date': base_date + timedelta(days=i * 5),
            'amount': 200.0,
            'type': 'deposit',
            'pending': 0
        })
    
    # Import transactions
    for txn in transactions:
        cursor.execute("""
            INSERT INTO transactions 
            (transaction_id, account_id, date, amount, pending)
            VALUES (?, ?, ?, ?, ?)
        """, (txn['transaction_id'], txn['account_id'], txn['date'], txn['amount'], txn['pending']))
    
    temp_db.conn.commit()
    
    # Detect savings signals
    result = detector.detect_savings_signals("test_savings", transactions, 30)
    
    assert 'savings_growth_rate' in result
    assert 'net_inflow' in result
    assert result['net_inflow'] > 0  # Should show positive inflow


def test_emergency_fund_coverage(temp_db):
    """Test emergency fund coverage calculation"""
    detector = SavingsDetector(temp_db.conn)
    
    # Create test user with savings and checking
    cursor = temp_db.conn.cursor()
    cursor.execute("INSERT INTO users (user_id, created_at, last_updated) VALUES (?, ?, ?)",
                   ("test_emergency", datetime.now(), datetime.now()))
    
    # Savings account with $6000
    cursor.execute("""
        INSERT INTO accounts (account_id, user_id, type, balance_current)
        VALUES (?, ?, ?, ?)
    """, ("acc_savings", "test_emergency", "savings", 6000.0))
    
    # Create transactions showing monthly expenses ~$2000
    base_date = datetime.now() - timedelta(days=30)
    transactions = []
    
    for i in range(6):
        transactions.append({
            'transaction_id': f"txn_{i}",
            'account_id': 'acc_savings',
            'date': base_date + timedelta(days=i * 5),
            'amount': -500.0,  # Expenses
            'type': 'purchase',
            'pending': 0
        })
    
    for txn in transactions:
        cursor.execute("""
            INSERT INTO transactions 
            (transaction_id, account_id, date, amount, pending)
            VALUES (?, ?, ?, ?, ?)
        """, (txn['transaction_id'], txn['account_id'], txn['date'], txn['amount'], txn['pending']))
    
    temp_db.conn.commit()
    
    # Detect savings signals
    result = detector.detect_savings_signals("test_emergency", transactions, 30)
    
    assert 'emergency_fund_months' in result
    # $6000 / ($2000/month) = 3 months
    assert result['emergency_fund_months'] >= 2.0

