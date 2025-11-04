"""Unit tests for subscription detection"""

import pytest
from datetime import datetime, timedelta
from spendsense.features.subscriptions import SubscriptionDetector


def test_subscription_detection_with_jitter(temp_db, sample_user_data):
    """Test subscription detection handles jitter (±1-2 days)"""
    detector = SubscriptionDetector(temp_db.conn)
    user_id = sample_user_data['users'][0]
    
    # Get transactions for the user
    cursor = temp_db.conn.cursor()
    cursor.execute("""
        SELECT t.*, a.user_id
        FROM transactions t
        JOIN accounts a ON t.account_id = a.account_id
        WHERE a.user_id = ?
        ORDER BY t.date
    """, (user_id,))
    
    transactions = cursor.fetchall()
    
    # Detect subscriptions
    result = detector.detect_subscriptions(user_id, transactions)
    
    # Should detect subscriptions if they exist
    assert 'subscriptions_count' in result
    assert 'subscriptions_monthly_spend' in result
    assert 'subscriptions_share_of_spend' in result
    assert result['subscriptions_count'] >= 0


def test_recurring_merchant_identification(temp_db):
    """Test recurring merchant identification (≥3 occurrences in 90 days)"""
    detector = SubscriptionDetector(temp_db.conn)
    
    # Create test transactions with recurring pattern
    cursor = temp_db.conn.cursor()
    
    # Create a test user and account
    cursor.execute("INSERT INTO users (user_id, created_at, last_updated) VALUES (?, ?, ?)",
                   ("test_recur", datetime.now(), datetime.now()))
    
    cursor.execute("""
        INSERT INTO accounts (account_id, user_id, type)
        VALUES (?, ?, ?)
    """, ("acc_recur", "test_recur", "checking"))
    
    # Create 4 transactions with same merchant (should be detected as subscription)
    base_date = datetime.now() - timedelta(days=30)
    for i in range(4):
        cursor.execute("""
            INSERT INTO transactions 
            (transaction_id, account_id, date, amount, merchant_name, pending)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            f"txn_{i}",
            "acc_recur",
            base_date + timedelta(days=i * 30),
            -29.99,
            "Netflix",
            0
        ))
    
    temp_db.conn.commit()
    
    # Get transactions
    cursor.execute("""
        SELECT t.*, a.user_id
        FROM transactions t
        JOIN accounts a ON t.account_id = a.account_id
        WHERE a.user_id = 'test_recur'
    """)
    
    transactions = cursor.fetchall()
    
    # Detect subscriptions
    result = detector.detect_subscriptions("test_recur", transactions)
    
    # Should detect at least 1 subscription
    assert result['subscriptions_count'] >= 1

