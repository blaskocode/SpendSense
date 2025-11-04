"""Eligibility checks for partner offers"""

from typing import List, Dict, Optional
import sqlite3

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class EligibilityChecker:
    """Checks eligibility for partner offers"""
    
    # Harmful products to filter out
    HARMFUL_PRODUCTS = [
        'payday loan',
        'payday lending',
        'title loan',
        'pawn shop',
        'predatory lending',
        'high-cost loan'
    ]
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize eligibility checker.
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
    
    def check_offer_eligibility(
        self,
        user_id: str,
        offer_title: str,
        offer_type: str,
        signals: Dict[str, any]
    ) -> tuple[bool, List[str]]:
        """Check if user is eligible for an offer.
        
        Args:
            user_id: User identifier
            offer_title: Offer title
            offer_type: Type of offer
            signals: Aggregated signals dictionary
            
        Returns:
            Tuple of (is_eligible, list_of_reasons)
        """
        reasons = []
        is_eligible = True
        
        # Check for harmful products
        if self._is_harmful_product(offer_title):
            reasons.append("Product filtered: Harmful financial product")
            return False, reasons
        
        # Check if user already has the product
        if self._user_has_product(user_id, offer_type, offer_title):
            reasons.append(f"User already has {offer_type}")
            return False, reasons
        
        # Check minimum requirements
        min_requirements = self._check_minimum_requirements(offer_type, signals)
        if not min_requirements[0]:
            reasons.extend(min_requirements[1])
            is_eligible = False
        
        return is_eligible, reasons
    
    def _is_harmful_product(self, offer_title: str) -> bool:
        """Check if product is in harmful products list.
        
        Args:
            offer_title: Offer title
            
        Returns:
            True if harmful, False otherwise
        """
        title_lower = offer_title.lower()
        return any(harmful in title_lower for harmful in self.HARMFUL_PRODUCTS)
    
    def _user_has_product(
        self,
        user_id: str,
        offer_type: str,
        offer_title: str
    ) -> bool:
        """Check if user already has the product.
        
        Args:
            user_id: User identifier
            offer_type: Type of offer
            offer_title: Offer title
            
        Returns:
            True if user has product, False otherwise
        """
        cursor = self.conn.cursor()
        
        if offer_type == "savings_account" and "high-yield" in offer_title.lower():
            # Check for money market or high-yield savings
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM accounts
                WHERE user_id = ? AND subtype IN ('money_market', 'hsa')
            """, (user_id,))
            return cursor.fetchone()['count'] > 0
        
        elif offer_type == "credit_card":
            # Check for credit cards
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM accounts
                WHERE user_id = ? AND type = 'credit'
            """, (user_id,))
            has_credit = cursor.fetchone()['count'] > 0
            
            # For secured cards, check if user already has credit
            if "secured" in offer_title.lower():
                return has_credit  # If they already have credit, don't need secured
            
            return False  # For other credit cards, having credit is OK
        
        elif offer_type == "app":
            # Simplified: Assume no existing apps (would need app tracking)
            return False
        
        return False
    
    def _check_minimum_requirements(
        self,
        offer_type: str,
        signals: Dict[str, any]
    ) -> tuple[bool, List[str]]:
        """Check minimum requirements for an offer.
        
        Args:
            offer_type: Type of offer
            signals: Aggregated signals dictionary
            
        Returns:
            Tuple of (meets_requirements, list_of_reasons)
        """
        reasons = []
        credit_signals = signals.get('credit', {})
        income_signals = signals.get('income', {})
        
        if offer_type == "credit_card":
            # Check credit score proxy (simplified)
            utilization = credit_signals.get('credit_utilization', 0.0)
            credit_score_proxy = 750 - (utilization * 2)  # Rough estimate
            
            if "balance transfer" in offer_type.lower():
                if credit_score_proxy < 650:
                    reasons.append(f"Credit score proxy {credit_score_proxy:.0f} below minimum 650")
                    return False, reasons
        
        elif offer_type == "savings_account":
            # No minimum requirements for savings accounts
            pass
        
        elif offer_type == "credit_card" and "secured" in offer_type.lower():
            # Secured cards require checking balance (checked elsewhere)
            pass
        
        return True, reasons
    
    def filter_offers(
        self,
        user_id: str,
        offers: List[Dict[str, any]],
        signals: Dict[str, any]
    ) -> List[Dict[str, any]]:
        """Filter offers based on eligibility.
        
        Args:
            user_id: User identifier
            offers: List of offer dictionaries
            signals: Aggregated signals dictionary
            
        Returns:
            Filtered list of eligible offers
        """
        eligible_offers = []
        
        for offer in offers:
            is_eligible, reasons = self.check_offer_eligibility(
                user_id,
                offer.get('title', ''),
                offer.get('offer_type', ''),
                signals
            )
            
            if is_eligible:
                eligible_offers.append(offer)
            else:
                logger.debug(
                    f"Offer '{offer.get('title')}' filtered for user {user_id}: "
                    f"{', '.join(reasons)}"
                )
        
        return eligible_offers

