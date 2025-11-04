"""Tone validation for recommendations"""

from typing import List, Tuple
import re

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ToneValidator:
    """Validates tone of recommendations to ensure no shaming language"""
    
    # Blocklist of shaming phrases (case-insensitive patterns)
    SHAMING_PHRASES = [
        r"you're overspending",
        r"you are overspending",
        r"you overspent",
        r"bad choices",
        r"poor choices",
        r"you're wasting money",
        r"you're bad with money",
        r"you're irresponsible",
        r"you're reckless",
        r"you should feel bad",
        r"you're terrible at",
        r"you fail at",
        r"you're horrible at",
        r"you're wrong",
        r"you're stupid",
        r"you're dumb",
        r"you're lazy",
        r"you're careless",
        r"you're foolish",
        r"you're incompetent",
        r"you're a failure",
        r"you're pathetic",
        r"you're hopeless",
        r"you're clueless",
        r"you're ignorant",
        r"you're uneducated",
        r"you're broke",
        r"you're poor",
        r"you're destitute",
        r"you're bankrupt",
        r"you're in debt",
        r"you're drowning in debt",
        r"you're buried in debt",
        r"you're a debtor",
        r"you're a deadbeat",
        r"you're a spendthrift",
        r"you're a wastrel",
        r"you're throwing away money",
        r"you're burning money",
        r"you're flushing money down the toilet",
        r"you're squandering",
        r"you're being wasteful",
        r"you're being irresponsible",
        r"you're being reckless",
        r"you're being foolish",
        r"you're being stupid",
        r"you're being dumb",
        r"you're being lazy",
        r"you're being careless",
        r"you're being incompetent",
        r"you're being a failure",
        r"you're being pathetic",
        r"you're being hopeless",
        r"you're being clueless",
        r"you're being ignorant",
        r"you're being uneducated",
        r"you're being broke",
        r"you're being poor",
        r"you're being destitute",
        r"you're being bankrupt",
        r"you're being in debt",
        r"you're being a debtor",
        r"you're being a deadbeat",
        r"you're being a spendthrift",
        r"you're being a wastrel",
    ]
    
    def __init__(self):
        """Initialize tone validator"""
        # Compile regex patterns for shaming phrases
        self.shaming_patterns = [
            re.compile(phrase, re.IGNORECASE) for phrase in self.SHAMING_PHRASES
        ]
    
    def validate_tone(self, text: str) -> Tuple[bool, List[str]]:
        """Validate tone of text.
        
        Args:
            text: Text to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        text_lower = text.lower()
        
        # Check for shaming phrases
        for pattern in self.shaming_patterns:
            if pattern.search(text_lower):
                issues.append(f"Shaming language detected: '{pattern.pattern}'")
        
        is_valid = len(issues) == 0
        
        if not is_valid:
            logger.warning(f"Tone validation failed: {', '.join(issues)}")
        
        return is_valid, issues
    
    def sanitize_text(self, text: str) -> str:
        """Sanitize text by replacing shaming phrases with positive alternatives.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text
        """
        sanitized = text
        
        for pattern in self.shaming_patterns:
            # Replace shaming phrases with neutral/positive alternatives
            # Pattern is already compiled with IGNORECASE flag
            sanitized = pattern.sub(
                "there's an opportunity to improve",
                sanitized
            )
        
        return sanitized
