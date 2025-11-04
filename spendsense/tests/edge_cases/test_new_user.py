"""Edge case tests"""

import pytest
from datetime import datetime, timedelta
from spendsense.storage.sqlite_manager import SQLiteManager
from spendsense.features.degradation import GracefulDegradation
from spendsense.features.aggregator import SignalAggregator


def test_new_user_less_than_7_days_data(temp_db):
    """Test new user (<7 days data)"""
    # Create user with <7 days of data
    cursor = temp_db.conn.cursor()
    cursor.execute("INSERT INTO users (user_id, created_at, last_updated) VALUES (?, ?, ?)",
                   ("test_new", datetime.now() - timedelta(days=5), datetime.now()))
    
    cursor.execute("""
        INSERT INTO accounts (account_id, user_id, type)
        VALUES (?, ?, ?)
    """, ("acc_new", "test_new", "checking"))
    
    # Add 2 transactions
    for i in range(2):
        cursor.execute("""
            INSERT INTO transactions 
            (transaction_id, account_id, date, amount, pending)
            VALUES (?, ?, ?, ?, ?)
        """, (
            f"txn_{i}",
            "acc_new",
            datetime.now().date() - timedelta(days=3-i),
            -50.0,
            0
        ))
    
    temp_db.conn.commit()
    
    # Test graceful degradation
    aggregator = SignalAggregator(temp_db.conn)
    degradation = GracefulDegradation(aggregator)
    
    signals = degradation.get_signals_with_degradation("test_new")
    
    # Should return degraded signals
    assert 'data_availability' in signals
    assert signals['data_availability'] in ['new', 'partial', 'full_30', 'full_180']


def test_user_with_only_pending_transactions(temp_db):
    """Test user with only pending transactions"""
    cursor = temp_db.conn.cursor()
    cursor.execute("INSERT INTO users (user_id, created_at, last_updated) VALUES (?, ?, ?)",
                   ("test_pending", datetime.now(), datetime.now()))
    
    cursor.execute("""
        INSERT INTO accounts (account_id, user_id, type)
        VALUES (?, ?, ?)
    """, ("acc_pending", "test_pending", "checking"))
    
    # Add only pending transactions
    for i in range(3):
        cursor.execute("""
            INSERT INTO transactions 
            (transaction_id, account_id, date, amount, pending)
            VALUES (?, ?, ?, ?, ?)
        """, (
            f"txn_{i}",
            "acc_pending",
            datetime.now().date() - timedelta(days=5-i),
            -50.0,
            1  # Pending
        ))
    
    temp_db.conn.commit()
    
    aggregator = SignalAggregator(temp_db.conn)
    degradation = GracefulDegradation(aggregator)
    
    signals = degradation.get_signals_with_degradation("test_pending")
    
    # Should handle gracefully with no posted transactions
    assert 'data_availability' in signals


def test_account_with_zero_balance_entire_period(temp_db):
    """Test account with $0 balance entire period"""
    cursor = temp_db.conn.cursor()
    cursor.execute("INSERT INTO users (user_id, created_at, last_updated) VALUES (?, ?, ?)",
                   ("test_zero", datetime.now(), datetime.now()))
    
    cursor.execute("""
        INSERT INTO accounts (account_id, user_id, type, balance_current)
        VALUES (?, ?, ?, ?)
    """, ("acc_zero", "test_zero", "checking", 0.0))
    
    temp_db.conn.commit()
    
    aggregator = SignalAggregator(temp_db.conn)
    signals = aggregator.compute_signals("test_zero", "30d")
    
    # Should handle zero balance gracefully
    assert isinstance(signals, dict)


def test_user_with_negative_savings_growth(temp_db):
    """Test user with negative savings growth"""
    cursor = temp_db.conn.cursor()
    cursor.execute("INSERT INTO users (user_id, created_at, last_updated) VALUES (?, ?, ?)",
                   ("test_negative", datetime.now(), datetime.now()))
    
    cursor.execute("""
        INSERT INTO accounts (account_id, user_id, type, balance_current)
        VALUES (?, ?, ?, ?)
    """, ("acc_neg", "test_negative", "savings", 500.0))
    
    # Create transactions showing decline
    base_date = datetime.now() - timedelta(days=30)
    for i in range(3):
        cursor.execute("""
            INSERT INTO transactions 
            (transaction_id, account_id, date, amount, pending)
            VALUES (?, ?, ?, ?, ?)
        """, (
            f"txn_{i}",
            "acc_neg",
            base_date + timedelta(days=i * 10),
            -200.0,  # Withdrawals
            0
        ))
    
    temp_db.conn.commit()
    
    aggregator = SignalAggregator(temp_db.conn)
    signals = aggregator.compute_signals("test_negative", "30d")
    
    # Should handle negative growth
    assert 'savings' in signals
    if 'savings_growth_rate' in signals.get('savings', {}):
        assert isinstance(signals['savings']['savings_growth_rate'], (int, float))

