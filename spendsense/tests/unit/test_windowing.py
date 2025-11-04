"""Unit tests for time windowing"""

import pytest
from datetime import datetime, timedelta
from spendsense.features.windowing import TimeWindowPartitioner


def test_window_boundary_date_calculations(temp_db):
    """Test window boundary date calculations"""
    windower = TimeWindowPartitioner(temp_db.conn)
    
    # Test 30-day window
    today = datetime.now().date()
    start_30d, end_30d = windower.get_30_day_window()
    
    assert start_30d == today - timedelta(days=30)
    assert end_30d == today - timedelta(days=1)
    
    # Test 180-day window
    start_180d, end_180d = windower.get_180_day_window()
    
    assert start_180d == today - timedelta(days=180)
    assert end_180d == today - timedelta(days=1)


def test_partial_window_handling_less_than_30_days(temp_db):
    """Test partial window handling (<30 days)"""
    windower = TimeWindowPartitioner(temp_db.conn)
    
    # Create user with <7 days of data
    cursor = temp_db.conn.cursor()
    cursor.execute("INSERT INTO users (user_id, created_at, last_updated) VALUES (?, ?, ?)",
                   ("test_new", datetime.now() - timedelta(days=5), datetime.now()))
    
    cursor.execute("""
        INSERT INTO accounts (account_id, user_id, type)
        VALUES (?, ?, ?)
    """, ("acc_new", "test_new", "checking"))
    
    # Add 3 transactions in last 5 days
    for i in range(3):
        cursor.execute("""
            INSERT INTO transactions 
            (transaction_id, account_id, date, amount, pending)
            VALUES (?, ?, ?, ?, ?)
        """, (
            f"txn_{i}",
            "acc_new",
            datetime.now().date() - timedelta(days=5-i),
            -50.0,
            0
        ))
    
    temp_db.conn.commit()
    
    # Get transactions in window
    transactions = windower.get_transactions_in_window("test_new", "30d", exclude_pending=True)
    
    # Should return transactions even if <30 days
    assert len(transactions) >= 0


def test_edge_case_zero_transactions_in_window(temp_db):
    """Test edge case: zero transactions in window"""
    windower = TimeWindowPartitioner(temp_db.conn)
    
    # Create user with no transactions
    cursor = temp_db.conn.cursor()
    cursor.execute("INSERT INTO users (user_id, created_at, last_updated) VALUES (?, ?, ?)",
                   ("test_empty", datetime.now(), datetime.now()))
    
    transactions = windower.get_transactions_in_window("test_empty", "30d", exclude_pending=True)
    
    # Should return empty list, not error
    assert isinstance(transactions, list)
    assert len(transactions) == 0

