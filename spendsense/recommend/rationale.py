"""Rationale generation for recommendations"""

from typing import Dict, List, Optional
from dataclasses import dataclass

from .catalog import EducationItem
from .offers import PartnerOffer
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class RationaleGenerator:
    """Generates plain-language rationales for recommendations"""
    
    def __init__(self):
        """Initialize rationale generator"""
        pass
    
    def generate_education_rationale(
        self,
        item: EducationItem,
        signals: Dict[str, any],
        persona_name: str
    ) -> str:
        """Generate rationale for an education item.
        
        Args:
            item: Education item
            signals: Aggregated signals dictionary
            persona_name: Assigned persona name
            
        Returns:
            Plain-language rationale string
        """
        credit_signals = signals.get('credit', {})
        subscriptions = signals.get('subscriptions', {})
        savings = signals.get('savings', {})
        income = signals.get('income', {})
        
        # Generate persona-specific rationales
        if persona_name == "High Utilization":
            return self._high_utilization_rationale(item, credit_signals)
        elif persona_name == "Variable Income Budgeter":
            return self._variable_income_rationale(item, income)
        elif persona_name == "Credit Builder":
            return self._credit_builder_rationale(item, credit_signals)
        elif persona_name == "Subscription-Heavy":
            return self._subscription_heavy_rationale(item, subscriptions)
        elif persona_name == "Savings Builder":
            return self._savings_builder_rationale(item, savings, credit_signals)
        else:
            return self._generic_rationale(item, persona_name)
    
    def generate_offer_rationale(
        self,
        offer: PartnerOffer,
        signals: Dict[str, any],
        user_id: str
    ) -> str:
        """Generate rationale for a partner offer.
        
        Args:
            offer: Partner offer
            signals: Aggregated signals dictionary
            user_id: User identifier
            
        Returns:
            Plain-language rationale string
        """
        credit_signals = signals.get('credit', {})
        subscriptions = signals.get('subscriptions', {})
        savings = signals.get('savings', {})
        
        if offer.offer_type == "credit_card" and "balance transfer" in offer.title.lower():
            utilization = credit_signals.get('credit_utilization', 0.0)
            interest = credit_signals.get('interest_charges', 0.0)
            return (
                f"We noticed your credit utilization is at {utilization:.1f}%. "
                f"A balance transfer card with 0% APR could help you save approximately "
                f"${interest:.2f}/month in interest charges while you pay down your debt."
            )
        
        elif offer.offer_type == "savings_account":
            growth_rate = savings.get('savings_growth_rate', 0.0)
            emergency_months = savings.get('emergency_fund_months', 0.0)
            return (
                f"Your savings are growing at {growth_rate:.1f}% and you have "
                f"{emergency_months:.1f} months of expenses covered. A high-yield savings account "
                f"could help you earn 4-5% APY, significantly more than traditional savings."
            )
        
        elif offer.offer_type == "app" and "subscription" in offer.title.lower():
            count = subscriptions.get('subscriptions_count', 0)
            monthly_spend = subscriptions.get('monthly_recurring_spend', 0.0)
            return (
                f"You have {count} active subscriptions totaling ${monthly_spend:.2f}/month. "
                f"A subscription management tool can help you track these services and identify "
                f"opportunities to save."
            )
        
        elif offer.offer_type == "credit_card" and "secured" in offer.title.lower():
            return (
                "A secured credit card is a great first step to building credit history. "
                "Your deposit secures the credit line, and responsible use will help establish "
                "your credit profile with all three major credit bureaus."
            )
        
        else:
            return f"This offer aligns with your financial goals and current situation."
    
    def _high_utilization_rationale(self, item: EducationItem, credit: Dict[str, any]) -> str:
        """Generate rationale for High Utilization persona"""
        utilization = credit.get('credit_utilization', 0.0)
        interest = credit.get('interest_charges', 0.0)
        
        if "debt" in item.title.lower() or "payoff" in item.title.lower():
            return (
                f"Your credit utilization is at {utilization:.1f}%, which is above the recommended 30%. "
                f"This content can help you develop a strategy to pay down your debt and "
                f"save approximately ${interest:.2f}/month in interest charges."
            )
        elif "utilization" in item.title.lower() or "score" in item.title.lower():
            return (
                f"Your current credit utilization of {utilization:.1f}% is impacting your credit score. "
                f"Reducing this to below 30% could improve your score and lower your interest rates."
            )
        elif "autopay" in item.title.lower():
            return (
                f"Setting up autopay can help you avoid late fees and improve your credit score. "
                f"With your current utilization at {utilization:.1f}%, on-time payments are especially important."
            )
        else:
            return (
                f"This content addresses your high credit utilization ({utilization:.1f}%) and can help "
                f"you reduce debt and improve your financial health."
            )
    
    def _variable_income_rationale(self, item: EducationItem, income: Dict[str, any]) -> str:
        """Generate rationale for Variable Income Budgeter persona"""
        pay_gap = income.get('median_pay_gap_days', 0)
        buffer = income.get('cash_flow_buffer_months', 0.0)
        
        if "budget" in item.title.lower():
            return (
                f"With {pay_gap} days between paychecks and only {buffer:.1f} months of cash buffer, "
                f"percent-based budgeting can help you manage irregular income more effectively."
            )
        elif "emergency" in item.title.lower():
            return (
                f"Your cash buffer is currently {buffer:.1f} months. Building a 3-month emergency fund "
                f"will provide stability when income is irregular."
            )
        else:
            return (
                f"This content addresses your variable income situation ({pay_gap} day pay gaps) and "
                f"can help you better manage cash flow."
            )
    
    def _credit_builder_rationale(self, item: EducationItem, credit: Dict[str, any]) -> str:
        """Generate rationale for Credit Builder persona"""
        utilization = credit.get('credit_utilization', 0.0)
        
        if "secured" in item.title.lower():
            return (
                "A secured credit card is an excellent first step to building credit. "
                "Your deposit secures the credit line, and responsible use will establish "
                "your credit history with all three major credit bureaus."
            )
        elif "credit 101" in item.title.lower() or "how credit works" in item.title.lower():
            return (
                "Understanding how credit works is essential for building a strong financial foundation. "
                "This content will help you learn the basics and make informed decisions."
            )
        else:
            return (
                "This content will help you build credit responsibly and understand how to use credit "
                "as a tool for financial growth."
            )
    
    def _subscription_heavy_rationale(self, item: EducationItem, subscriptions: Dict[str, any]) -> str:
        """Generate rationale for Subscription-Heavy persona"""
        count = subscriptions.get('subscriptions_count', 0)
        monthly_spend = subscriptions.get('monthly_recurring_spend', 0.0)
        
        if "audit" in item.title.lower():
            return (
                f"You have {count} active subscriptions totaling ${monthly_spend:.2f}/month. "
                f"An audit can help you identify services you may no longer need and save money."
            )
        elif "negotiate" in item.title.lower():
            return (
                f"With ${monthly_spend:.2f}/month in subscription costs, negotiating lower rates "
                f"could save you $10-50/month on your bills."
            )
        else:
            return (
                f"This content addresses your {count} active subscriptions and can help you "
                f"optimize your recurring expenses."
            )
    
    def _savings_builder_rationale(
        self, 
        item: EducationItem, 
        savings: Dict[str, any],
        credit: Dict[str, any]
    ) -> str:
        """Generate rationale for Savings Builder persona"""
        growth_rate = savings.get('savings_growth_rate', 0.0)
        monthly_inflow = savings.get('net_savings_inflow', 0.0)
        utilization = credit.get('credit_utilization', 0.0)
        
        if "goal" in item.title.lower():
            return (
                f"Your savings are growing at {growth_rate:.1f}% with ${monthly_inflow:.2f}/month in new savings. "
                f"Setting SMART goals can help you maximize this growth."
            )
        elif "automate" in item.title.lower():
            return (
                f"Automating your savings can help you maintain your current growth rate of {growth_rate:.1f}% "
                f"without having to think about it."
            )
        elif "high-yield" in item.title.lower() or "hysa" in item.title.lower():
            return (
                f"With your healthy savings habits (${monthly_inflow:.2f}/month), a high-yield savings account "
                f"could help you earn 4-5% APY instead of the typical 0.01-0.5%."
            )
        else:
            return (
                f"This content builds on your strong savings foundation ({growth_rate:.1f}% growth) "
                f"and can help you optimize your financial strategy."
            )
    
    def _generic_rationale(self, item: EducationItem, persona_name: str) -> str:
        """Generate generic rationale when persona-specific logic doesn't apply"""
        return f"This content is tailored to your {persona_name} profile and can help you achieve your financial goals."

