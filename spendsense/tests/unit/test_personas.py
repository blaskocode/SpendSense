"""Unit tests for persona assignment"""

import pytest
from spendsense.personas.criteria import PersonaMatcher
from spendsense.personas.prioritization import PersonaPrioritizer


def test_high_utilization_persona_criteria(temp_db):
    """Test High Utilization persona criteria (priority 1)"""
    matcher = PersonaMatcher()
    
    # Test case: utilization ≥50%
    signals_30d = {
        'credit': {
            'credit_utilization': 55.0,
            'interest_charges': 0.0,
            'min_payment_only': False,
            'overdue': False
        }
    }
    
    result = matcher.match_all_personas(signals_30d, signals_30d, account_types=['credit_card'])
    
    assert 'High Utilization' in result
    assert result['High Utilization']['priority'] == 1


def test_variable_income_persona_criteria(temp_db):
    """Test Variable Income Budgeter persona criteria (priority 2)"""
    matcher = PersonaMatcher()
    
    # Test case: pay gap >45d AND cash buffer <1 month
    signals_30d = {
        'income': {
            'payroll_detected': True,
            'pay_gap_days': 50,
            'cash_buffer_months': 0.5
        }
    }
    
    result = matcher.match_all_personas(signals_30d, signals_30d, account_types=['checking'])
    
    assert 'Variable Income Budgeter' in result
    assert result['Variable Income Budgeter']['priority'] == 2


def test_credit_builder_persona_criteria(temp_db):
    """Test Credit Builder persona criteria (priority 3)"""
    matcher = PersonaMatcher()
    
    # Test case: no credit OR $0 balance 180+ days AND has checking/savings
    signals_30d = {
        'credit': {
            'credit_utilization': 0.0,
            'has_active_credit': False
        }
    }
    signals_180d = {
        'credit': {
            'credit_utilization': 0.0
        }
    }
    
    result = matcher.match_all_personas(signals_30d, signals_180d, account_types=['checking', 'savings'])
    
    assert 'Credit Builder' in result
    assert result['Credit Builder']['priority'] == 3


def test_subscription_heavy_persona_criteria(temp_db):
    """Test Subscription-Heavy persona criteria (priority 4)"""
    matcher = PersonaMatcher()
    
    # Test case: recurring ≥3 AND (monthly spend ≥$50 OR share ≥10%)
    signals_30d = {
        'subscriptions': {
            'subscriptions_count': 4,
            'subscriptions_monthly_spend': 75.0,
            'subscriptions_share_of_spend': 12.0
        }
    }
    
    result = matcher.match_all_personas(signals_30d, signals_30d, account_types=['checking'])
    
    assert 'Subscription-Heavy' in result
    assert result['Subscription-Heavy']['priority'] == 4


def test_savings_builder_persona_criteria(temp_db):
    """Test Savings Builder persona criteria (priority 5)"""
    matcher = PersonaMatcher()
    
    # Test case: growth ≥2% OR inflow ≥$200/mo AND utilization <30%
    signals_30d = {
        'savings': {
            'savings_growth_rate': 3.0,
            'net_inflow': 250.0
        },
        'credit': {
            'credit_utilization': 25.0
        }
    }
    
    result = matcher.match_all_personas(signals_30d, signals_30d, account_types=['checking', 'savings'])
    
    assert 'Savings Builder' in result
    assert result['Savings Builder']['priority'] == 5

