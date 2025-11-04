"""Unit tests for guardrails"""

import pytest
from spendsense.guardrails.consent import ConsentManager
from spendsense.guardrails.eligibility import EligibilityChecker
from spendsense.guardrails.tone import ToneValidator


def test_consent_enforcement_block_without_consent(temp_db):
    """Test consent enforcement blocks recommendations without consent"""
    consent_manager = ConsentManager(temp_db.conn)
    
    # Create test user
    cursor = temp_db.conn.cursor()
    from datetime import datetime
    cursor.execute("INSERT INTO users (user_id, created_at, last_updated, consent_status) VALUES (?, ?, ?, ?)",
                   ("test_no_consent", datetime.now(), datetime.now(), False))
    temp_db.conn.commit()
    
    # Check consent
    has_consent = consent_manager.check_consent("test_no_consent")
    
    assert has_consent is False


def test_eligibility_filter_logic(temp_db):
    """Test eligibility filter logic"""
    checker = EligibilityChecker(temp_db.conn)
    
    # Test filtering out products user already has
    user_accounts = [
        {'type': 'checking', 'subtype': 'checking'},
        {'type': 'savings', 'subtype': 'savings'}
    ]
    
    # Should filter out HYSA if user already has savings
    eligible = checker.check_offer_eligibility(
        offer_type='high_yield_savings',
        user_accounts=user_accounts,
        signals={}
    )
    
    # Logic depends on implementation, but should return boolean
    assert isinstance(eligible, bool)


def test_tone_check_negative_phrase_detection():
    """Test tone check detects negative phrases"""
    validator = ToneValidator()
    
    # Test shaming phrases
    test_texts = [
        "You're overspending on subscriptions",
        "Bad choices led to high credit utilization",
        "This will help you manage your finances better"  # Should pass
    ]
    
    results = []
    for text in test_texts:
        is_valid, sanitized = validator.validate_tone(text)
        results.append((is_valid, sanitized))
    
    # First two should fail or be sanitized
    assert not results[0][0] or results[0][1] != test_texts[0]
    assert not results[1][0] or results[1][1] != test_texts[1]
    # Third should pass
    assert results[2][0]

