"""Disclosure injection for recommendations"""

from typing import List, Dict

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class DisclosureInjector:
    """Injects required disclosures into recommendations"""
    
    DISCLOSURE_TEXT = (
        "This is educational content, not financial advice. "
        "Consult a licensed financial advisor for personalized guidance."
    )
    
    def __init__(self):
        """Initialize disclosure injector"""
        pass
    
    def inject_disclosure(self, recommendation: Dict[str, any]) -> Dict[str, any]:
        """Inject disclosure into a recommendation.
        
        Args:
            recommendation: Recommendation dictionary
            
        Returns:
            Recommendation with disclosure added
        """
        # Add disclosure to rationale
        rationale = recommendation.get('rationale', '')
        if self.DISCLOSURE_TEXT not in rationale:
            recommendation['rationale'] = f"{rationale}\n\n{self.DISCLOSURE_TEXT}"
            recommendation['disclosure'] = self.DISCLOSURE_TEXT
        
        return recommendation
    
    def inject_disclosure_batch(
        self,
        recommendations: List[Dict[str, any]]
    ) -> List[Dict[str, any]]:
        """Inject disclosure into a batch of recommendations.
        
        Args:
            recommendations: List of recommendation dictionaries
            
        Returns:
            List of recommendations with disclosures added
        """
        return [self.inject_disclosure(rec) for rec in recommendations]
    
    def get_disclosure_text(self) -> str:
        """Get the standard disclosure text.
        
        Returns:
            Disclosure text string
        """
        return self.DISCLOSURE_TEXT

