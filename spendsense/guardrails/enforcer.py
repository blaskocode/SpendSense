"""Guardrails enforcement orchestrator"""

from typing import List, Dict
import sqlite3

from .consent import ConsentManager
from .eligibility import EligibilityChecker
from .tone import ToneValidator
from .disclosure import DisclosureInjector
from ..utils.logger import setup_logger
from ..utils.errors import ConsentError

logger = setup_logger(__name__)


class GuardrailsEnforcer:
    """Enforces all guardrails on recommendations"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize guardrails enforcer.
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
        self.consent_manager = ConsentManager(db_connection)
        self.eligibility_checker = EligibilityChecker(db_connection)
        self.tone_validator = ToneValidator()
        self.disclosure_injector = DisclosureInjector()
    
    def enforce_guardrails(
        self,
        user_id: str,
        recommendations: List[Dict[str, any]],
        signals: Dict[str, any]
    ) -> List[Dict[str, any]]:
        """Enforce all guardrails on recommendations.
        
        Args:
            user_id: User identifier
            recommendations: List of recommendations
            signals: Aggregated signals dictionary
            
        Returns:
            Filtered list of recommendations with guardrails applied
            
        Raises:
            ConsentError: If user does not have active consent
        """
        # Step 1: Check consent
        if not self.consent_manager.check_consent(user_id):
            logger.warning(f"User {user_id} does not have consent - blocking recommendations")
            return []  # Return empty list if no consent
        
        # Step 2: Filter by eligibility (for offers)
        filtered_recommendations = []
        
        for rec in recommendations:
            if rec.get('type') == 'offer':
                # Check eligibility for offers
                is_eligible, reasons = self.eligibility_checker.check_offer_eligibility(
                    user_id,
                    rec.get('title', ''),
                    rec.get('offer_type', ''),
                    signals
                )
                
                if not is_eligible:
                    logger.debug(
                        f"Offer '{rec.get('title')}' filtered for user {user_id}: "
                        f"{', '.join(reasons)}"
                    )
                    continue
            
            # Step 3: Validate tone
            rationale = rec.get('rationale', '')
            is_valid_tone, tone_issues = self.tone_validator.validate_tone(rationale)
            
            if not is_valid_tone:
                # Sanitize text instead of blocking
                rec['rationale'] = self.tone_validator.sanitize_text(rationale)
                logger.info(f"Tone sanitized for recommendation '{rec.get('title')}'")
            
            # Step 4: Inject disclosure
            rec = self.disclosure_injector.inject_disclosure(rec)
            
            filtered_recommendations.append(rec)
        
        logger.info(
            f"Guardrails enforced for user {user_id}: "
            f"{len(filtered_recommendations)}/{len(recommendations)} recommendations passed"
        )
        
        return filtered_recommendations
    
    def require_consent_for_processing(self, user_id: str) -> None:
        """Require active consent before processing.
        
        Args:
            user_id: User identifier
            
        Raises:
            ConsentError: If user does not have active consent
        """
        self.consent_manager.require_consent(user_id)

