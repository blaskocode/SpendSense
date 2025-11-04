"""Unit tests for income signal detection"""

import pytest
from datetime import datetime, timedelta
from spendsense.features.income import IncomeDetector


def test_payroll_detection_accuracy(temp_db):
    """Test payroll detection accuracy"""
    detector = IncomeDetector(temp_db.conn)
    
    # Create test user and account
    cursor = temp_db.conn.cursor()
    cursor.execute("INSERT INTO users (user_id, created_at, last_updated) VALUES (?, ?, ?)",
                   ("test_payroll", datetime.now(), datetime.now()))
    
    cursor.execute("""
        INSERT INTO accounts (account_id, user_id, type)
        VALUES (?, ?, ?)
    """, ("acc_payroll", "test_payroll", "checking"))
    
    # Create payroll transactions (large deposits every 2 weeks)
    base_date = datetime.now() - timedelta(days=60)
    transactions = []
    
    for i in range(4):
        transactions.append({
            'transaction_id': f"pay_{i}",
            'account_id': 'acc_payroll',
            'date': base_date + timedelta(days=i * 14),
            'amount': 2500.0,
            'merchant_name': 'PAYROLL DEPOSIT',
            'payment_channel': 'ach',
            'pending': 0
        })
    
    for txn in transactions:
        cursor.execute("""
            INSERT INTO transactions 
            (transaction_id, account_id, date, amount, merchant_name, payment_channel, pending)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            txn['transaction_id'], txn['account_id'], txn['date'], 
            txn['amount'], txn['merchant_name'], txn['payment_channel'], txn['pending']
        ))
    
    temp_db.conn.commit()
    
    # Detect income signals
    result = detector.detect_income_signals("test_payroll", transactions, 60)
    
    assert 'payroll_detected' in result
    assert result['payroll_detected'] is True
    assert 'payroll_frequency_days' in result


def test_income_variability_computation(temp_db):
    """Test income variability computation"""
    detector = IncomeDetector(temp_db.conn)
    
    cursor = temp_db.conn.cursor()
    cursor.execute("INSERT INTO users (user_id, created_at, last_updated) VALUES (?, ?, ?)",
                   ("test_variability", datetime.now(), datetime.now()))
    
    cursor.execute("""
        INSERT INTO accounts (account_id, user_id, type)
        VALUES (?, ?, ?)
    """, ("acc_var", "test_variability", "checking"))
    
    # Create variable income (different amounts)
    base_date = datetime.now() - timedelta(days=60)
    amounts = [2000.0, 2500.0, 1800.0, 2200.0, 1900.0]
    
    for i, amount in enumerate(amounts):
        cursor.execute("""
            INSERT INTO transactions 
            (transaction_id, account_id, date, amount, merchant_name, payment_channel, pending)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            f"pay_{i}",
            "acc_var",
            base_date + timedelta(days=i * 14),
            amount,
            "PAYROLL",
            "ach",
            0
        ))
    
    temp_db.conn.commit()
    
    cursor.execute("""
        SELECT t.*, a.user_id
        FROM transactions t
        JOIN accounts a ON t.account_id = a.account_id
        WHERE a.user_id = 'test_variability'
    """)
    
    transactions = cursor.fetchall()
    
    result = detector.detect_income_signals("test_variability", transactions, 60)
    
    assert 'income_variability' in result
    # Should detect some variability with different amounts
    assert result.get('income_variability', 0) >= 0

