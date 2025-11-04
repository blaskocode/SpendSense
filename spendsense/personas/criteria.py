"""Persona matching criteria"""

from typing import Dict, List, Optional
from enum import Enum

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class Persona(Enum):
    """Persona types with priority levels"""
    HIGH_UTILIZATION = ("High Utilization", 1)
    VARIABLE_INCOME = ("Variable Income Budgeter", 2)
    CREDIT_BUILDER = ("Credit Builder", 3)
    SUBSCRIPTION_HEAVY = ("Subscription-Heavy", 4)
    SAVINGS_BUILDER = ("Savings Builder", 5)
    
    def __init__(self, display_name: str, priority: int):
        self.display_name = display_name
        self.priority = priority


class PersonaMatcher:
    """Matches users to personas based on behavioral signals"""
    
    def __init__(self):
        """Initialize persona matcher"""
        pass
    
    def match_personas(self, signals: Dict[str, any]) -> List[Persona]:
        """Match user signals to all applicable personas.
        
        Args:
            signals: Aggregated signals dictionary from SignalAggregator
            
        Returns:
            List of matching personas (may be multiple)
        """
        matching_personas = []
        
        # Extract signal components
        credit_signals = signals.get('credit', {})
        subscriptions = signals.get('subscriptions', {})
        savings = signals.get('savings', {})
        income = signals.get('income', {})
        
        # Priority 1: High Utilization
        if self._matches_high_utilization(credit_signals):
            matching_personas.append(Persona.HIGH_UTILIZATION)
        
        # Priority 2: Variable Income Budgeter
        if self._matches_variable_income(income):
            matching_personas.append(Persona.VARIABLE_INCOME)
        
        # Priority 3: Credit Builder
        if self._matches_credit_builder(signals):
            matching_personas.append(Persona.CREDIT_BUILDER)
        
        # Priority 4: Subscription-Heavy
        if self._matches_subscription_heavy(subscriptions):
            matching_personas.append(Persona.SUBSCRIPTION_HEAVY)
        
        # Priority 5: Savings Builder
        if self._matches_savings_builder(savings, credit_signals):
            matching_personas.append(Persona.SAVINGS_BUILDER)
        
        logger.debug(
            f"Matched {len(matching_personas)} personas: "
            f"{[p.display_name for p in matching_personas]}"
        )
        
        return matching_personas
    
    def _matches_high_utilization(self, credit_signals: Dict[str, any]) -> bool:
        """Check if user matches High Utilization persona.
        
        Criteria: utilization ≥50% OR interest > 0 OR min-payment-only OR overdue
        """
        utilization = credit_signals.get('credit_utilization', 0.0)
        interest_charges = credit_signals.get('interest_charges', 0.0)
        min_payment_only = credit_signals.get('min_payment_only', False)
        is_overdue = credit_signals.get('is_overdue', False)
        
        return (
            utilization >= 50.0 or
            interest_charges > 0 or
            min_payment_only or
            is_overdue
        )
    
    def _matches_variable_income(self, income_signals: Dict[str, any]) -> bool:
        """Check if user matches Variable Income Budgeter persona.
        
        Criteria: median pay gap > 45 days AND cash-flow buffer < 1 month
        """
        median_pay_gap = income_signals.get('median_pay_gap_days', 0)
        cash_buffer = income_signals.get('cash_flow_buffer_months', 0.0)
        
        return median_pay_gap > 45 and cash_buffer < 1.0
    
    def _matches_credit_builder(self, signals: Dict[str, any]) -> bool:
        """Check if user matches Credit Builder persona.
        
        Criteria: No credit card accounts OR all cards $0 balance for 180+ days,
        AND has checking/savings accounts
        
        Note: This uses signals which should already account for account existence
        """
        credit_signals_data = signals.get('credit', {})
        utilization = credit_signals_data.get('credit_utilization', 0.0)
        
        # Credit builder if:
        # 1. No credit utilization (implies no credit cards or $0 balance)
        # 2. No credit flags indicating active usage
        has_credit_usage = (
            utilization > 0 or
            credit_signals_data.get('utilization_30_flag', False) or
            credit_signals_data.get('utilization_50_flag', False) or
            credit_signals_data.get('utilization_80_flag', False) or
            credit_signals_data.get('interest_charges', 0.0) > 0
        )
        
        # Credit builder if no active credit usage
        # Note: Full check would verify checking/savings accounts exist,
        # but that's handled at assignment level with account data
        return not has_credit_usage
    
    def _matches_subscription_heavy(self, subscriptions: Dict[str, any]) -> bool:
        """Check if user matches Subscription-Heavy persona.
        
        Criteria: recurring merchants ≥3 AND (monthly spend ≥$50 OR share ≥10%)
        """
        count = subscriptions.get('subscriptions_count', 0)
        monthly_spend = subscriptions.get('monthly_recurring_spend', 0.0)
        spend_share = subscriptions.get('recurring_spend_share', 0.0)
        
        return (
            count >= 3 and
            (monthly_spend >= 50.0 or spend_share >= 10.0)
        )
    
    def _matches_savings_builder(self, savings: Dict[str, any], credit_signals: Dict[str, any]) -> bool:
        """Check if user matches Savings Builder persona.
        
        Criteria: (growth rate ≥2% OR inflow ≥$200/month) AND utilization <30%
        """
        growth_rate = savings.get('savings_growth_rate', 0.0)
        monthly_inflow = savings.get('net_savings_inflow', 0.0)
        utilization = credit_signals.get('credit_utilization', 0.0)
        
        savings_positive = (growth_rate >= 2.0 or monthly_inflow >= 200.0)
        credit_healthy = utilization < 30.0
        
        return savings_positive and credit_healthy

