"""Partner offers generation"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import sqlite3

from ..personas.criteria import Persona
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class PartnerOffer:
    """Partner offer item"""
    title: str
    description: str
    offer_type: str
    eligibility_requirements: List[str]
    estimated_benefit: str


class OfferGenerator:
    """Generates eligible partner offers"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize offer generator.
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
        self._offers = self._build_offer_catalog()
    
    def generate_offers(
        self,
        user_id: str,
        persona_name: str,
        signals: Dict[str, any],
        max_offers: int = 3
    ) -> List[PartnerOffer]:
        """Generate eligible partner offers for a user.
        
        Args:
            user_id: User identifier
            persona_name: Assigned persona name
            signals: Aggregated signals dictionary
            max_offers: Maximum number of offers to return
            
        Returns:
            List of eligible partner offers
        """
        eligible_offers = []
        
        credit_signals = signals.get('credit', {})
        subscriptions = signals.get('subscriptions', {})
        savings = signals.get('savings', {})
        income = signals.get('income', {})
        
        # Check each offer type
        for offer_type, offer_data in self._offers.items():
            if self._check_eligibility(
                offer_type, user_id, persona_name, signals,
                credit_signals, subscriptions, savings, income
            ):
                eligible_offers.append(offer_data)
        
        # Return up to max_offers
        return eligible_offers[:max_offers]
    
    def _check_eligibility(
        self,
        offer_type: str,
        user_id: str,
        persona_name: str,
        signals: Dict[str, any],
        credit_signals: Dict[str, any],
        subscriptions: Dict[str, any],
        savings: Dict[str, any],
        income: Dict[str, any]
    ) -> bool:
        """Check if user is eligible for an offer type.
        
        Args:
            offer_type: Type of offer to check
            user_id: User identifier
            persona_name: Assigned persona
            signals: Full signals dictionary
            credit_signals: Credit signals
            subscriptions: Subscription signals
            savings: Savings signals
            income: Income signals
            
        Returns:
            True if eligible, False otherwise
        """
        if offer_type == "balance_transfer_card":
            utilization = credit_signals.get('credit_utilization', 0.0)
            # Simplified: assume credit score proxy based on utilization
            # Real implementation would check actual credit score
            credit_score_proxy = 750 - (utilization * 2)  # Rough estimate
            return utilization >= 30.0 and credit_score_proxy >= 650
        
        elif offer_type == "high_yield_savings":
            # Check if building emergency fund (savings growth or low buffer)
            emergency_fund_months = savings.get('emergency_fund_months', 0.0)
            savings_growth = savings.get('savings_growth_rate', 0.0)
            building_emergency = emergency_fund_months < 3.0 or savings_growth > 0
            
            # Check if user already has HYSA (simplified check)
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM accounts
                WHERE user_id = ? AND subtype = 'money_market'
            """, (user_id,))
            has_money_market = cursor.fetchone()['count'] > 0
            
            return building_emergency and not has_money_market
        
        elif offer_type == "budgeting_app":
            # Check if variable income persona
            is_variable_income = persona_name == "Variable Income Budgeter"
            # Simplified: assume no existing linked app
            # Real implementation would check for linked apps
            return is_variable_income
        
        elif offer_type == "subscription_tool":
            subscription_count = subscriptions.get('subscriptions_count', 0)
            return subscription_count >= 5
        
        elif offer_type == "subscription_audit_service":
            # For Subscription-Heavy persona with any subscriptions
            subscription_count = subscriptions.get('subscriptions_count', 0)
            is_subscription_heavy = persona_name == "Subscription-Heavy"
            return is_subscription_heavy and subscription_count >= 2
        
        elif offer_type == "secured_credit_card":
            # Check if credit builder persona
            is_credit_builder = persona_name == "Credit Builder"
            
            # Check checking account balance
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT SUM(balance_current) as total_balance
                FROM accounts
                WHERE user_id = ? AND type = 'depository' AND subtype = 'checking'
            """, (user_id,))
            checking_balance = cursor.fetchone()['total_balance'] or 0.0
            
            return is_credit_builder and checking_balance >= 500.0
        
        return False
    
    def _build_offer_catalog(self) -> Dict[str, PartnerOffer]:
        """Build the partner offer catalog"""
        return {
            "balance_transfer_card": PartnerOffer(
                title="Balance Transfer Credit Card",
                description="Transfer high-interest debt to a card with 0% APR for 15-18 months. Save on interest while paying down debt.",
                offer_type="credit_card",
                eligibility_requirements=["Credit utilization ≥30%", "Credit score ≥650"],
                estimated_benefit="Save $50-200/month on interest charges"
            ),
            "high_yield_savings": PartnerOffer(
                title="High-Yield Savings Account",
                description="Earn 4-5% APY on your savings compared to traditional savings accounts. FDIC insured up to $250,000.",
                offer_type="savings_account",
                eligibility_requirements=["Building emergency fund", "No existing HYSA"],
                estimated_benefit="Earn $100-500/year more on savings"
            ),
            "budgeting_app": PartnerOffer(
                title="Budgeting App Subscription",
                description="Track income, expenses, and savings goals with automated categorization. Perfect for variable income earners.",
                offer_type="app",
                eligibility_requirements=["Variable income", "No existing budgeting app"],
                estimated_benefit="Save 2-3 hours/month on budgeting"
            ),
            "subscription_tool": PartnerOffer(
                title="Subscription Management Tool",
                description="Track all your subscriptions in one place, get alerts for price changes, and find cancellation opportunities.",
                offer_type="app",
                eligibility_requirements=["5+ active subscriptions"],
                estimated_benefit="Save $20-50/month on unused subscriptions"
            ),
            "secured_credit_card": PartnerOffer(
                title="Secured Credit Card",
                description="Build credit history with a secured card that reports to all three credit bureaus. Your deposit secures the credit line.",
                offer_type="credit_card",
                eligibility_requirements=["Credit builder persona", "Checking balance ≥$500"],
                estimated_benefit="Build credit score 50-100 points in 6-12 months"
            ),
            "subscription_audit_service": PartnerOffer(
                title="Subscription Audit Service",
                description="Professional review of your subscriptions with personalized recommendations. Identify hidden costs and cancellation opportunities.",
                offer_type="service",
                eligibility_requirements=["Subscription-Heavy persona", "2+ active subscriptions"],
                estimated_benefit="Save $50-150/month on subscriptions"
            )
        }

