"""AI consent management and enforcement"""

from typing import Optional
from datetime import datetime
import sqlite3

from ..utils.logger import setup_logger
from ..utils.errors import ConsentError

logger = setup_logger(__name__)


class AIConsentManager:
    """Manages user consent for AI-powered features"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize AI consent manager.
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
    
    def check_ai_consent(self, user_id: str) -> bool:
        """Check if user has active AI consent.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if user has active AI consent, False otherwise
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT ai_consent_status
            FROM users
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        
        if result:
            return bool(result['ai_consent_status'])
        
        return False
    
    def grant_ai_consent(self, user_id: str) -> None:
        """Grant user AI consent (opt-in).
        
        Args:
            user_id: User identifier
            
        Raises:
            ConsentError: If user not found
        """
        cursor = self.conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute("""
            UPDATE users
            SET ai_consent_status = TRUE,
                ai_consent_granted_at = ?,
                ai_consent_revoked_at = NULL,
                last_updated = ?
            WHERE user_id = ?
        """, (timestamp, timestamp, user_id))
        
        if cursor.rowcount == 0:
            raise ConsentError(f"User {user_id} not found")
        
        self.conn.commit()
        logger.info(f"AI consent granted for user {user_id}")
    
    def revoke_ai_consent(self, user_id: str) -> None:
        """Revoke user AI consent (opt-out).
        
        Args:
            user_id: User identifier
            
        Raises:
            ConsentError: If user not found
        """
        cursor = self.conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute("""
            UPDATE users
            SET ai_consent_status = FALSE,
                ai_consent_revoked_at = ?,
                last_updated = ?
            WHERE user_id = ?
        """, (timestamp, timestamp, user_id))
        
        if cursor.rowcount == 0:
            raise ConsentError(f"User {user_id} not found")
        
        # Delete AI-generated plans (immediate effect)
        cursor.execute("""
            DELETE FROM ai_plans
            WHERE user_id = ?
        """, (user_id,))
        
        self.conn.commit()
        logger.info(f"AI consent revoked for user {user_id}, AI plans deleted")
    
    def require_ai_consent(self, user_id: str) -> None:
        """Require active AI consent before proceeding.
        
        Args:
            user_id: User identifier
            
        Raises:
            ConsentError: If user does not have active AI consent
        """
        if not self.check_ai_consent(user_id):
            raise ConsentError(
                f"User {user_id} has not provided AI consent. "
                "Explicit opt-in required before using AI-powered features."
            )

