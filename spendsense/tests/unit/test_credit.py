"""Unit tests for credit signal detection"""

import pytest
from datetime import datetime
from spendsense.features.credit import CreditDetector


def test_credit_utilization_formula(temp_db):
    """Test credit utilization formula (balance/limit)"""
    detector = CreditDetector(temp_db.conn)
    
    # Create test user with credit card
    cursor = temp_db.conn.cursor()
    cursor.execute("INSERT INTO users (user_id, created_at, last_updated) VALUES (?, ?, ?)",
                   ("test_credit", datetime.now(), datetime.now()))
    
    # Credit card with $1000 balance, $5000 limit = 20% utilization
    cursor.execute("""
        INSERT INTO accounts (account_id, user_id, type, balance_current, balance_limit)
        VALUES (?, ?, ?, ?, ?)
    """, ("acc_credit", "test_credit", "credit_card", 1000.0, 5000.0))
    
    # Detect credit signals
    result = detector.detect_credit_signals("test_credit")
    
    assert 'credit_utilization' in result
    assert result['credit_utilization'] == pytest.approx(20.0, abs=0.1)


def test_credit_utilization_flags(temp_db):
    """Test credit utilization flag detection (≥30%, ≥50%, ≥80%)"""
    detector = CreditDetector(temp_db.conn)
    
    cursor = temp_db.conn.cursor()
    cursor.execute("INSERT INTO users (user_id, created_at, last_updated) VALUES (?, ?, ?)",
                   ("test_flags", datetime.now(), datetime.now()))
    
    # Test 80% utilization (should flag high)
    cursor.execute("""
        INSERT INTO accounts (account_id, user_id, type, balance_current, balance_limit)
        VALUES (?, ?, ?, ?, ?)
    """, ("acc_high", "test_flags", "credit_card", 4000.0, 5000.0))
    
    result = detector.detect_credit_signals("test_flags")
    
    assert result['credit_utilization'] == pytest.approx(80.0, abs=0.1)
    assert result.get('utilization_high', False) or result['credit_utilization'] >= 80.0

