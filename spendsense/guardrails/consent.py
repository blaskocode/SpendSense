"""Consent management and enforcement"""

from typing import Optional
from datetime import datetime
import sqlite3

from ..utils.logger import setup_logger
from ..utils.errors import ConsentError

logger = setup_logger(__name__)


class ConsentManager:
    """Manages user consent for data processing and recommendations"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize consent manager.
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
    
    def check_consent(self, user_id: str) -> bool:
        """Check if user has active consent.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if user has active consent, False otherwise
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT consent_status
            FROM users
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        
        if result:
            return bool(result['consent_status'])
        
        return False
    
    def record_consent(self, user_id: str) -> None:
        """Record user consent (opt-in).
        
        Args:
            user_id: User identifier
            
        Raises:
            DataError: If user not found
        """
        cursor = self.conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute("""
            UPDATE users
            SET consent_status = TRUE,
                consent_timestamp = ?,
                last_updated = ?
            WHERE user_id = ?
        """, (timestamp, timestamp, user_id))
        
        if cursor.rowcount == 0:
            raise ConsentError(f"User {user_id} not found")
        
        self.conn.commit()
        logger.info(f"Consent recorded for user {user_id}")
    
    def revoke_consent(self, user_id: str) -> None:
        """Revoke user consent (opt-out).
        
        Args:
            user_id: User identifier
            
        Raises:
            DataError: If user not found
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            UPDATE users
            SET consent_status = FALSE,
                consent_timestamp = NULL,
                last_updated = ?
            WHERE user_id = ?
        """, (datetime.now().isoformat(), user_id))
        
        if cursor.rowcount == 0:
            raise ConsentError(f"User {user_id} not found")
        
        # Delete all recommendations (immediate effect)
        cursor.execute("""
            DELETE FROM recommendations
            WHERE user_id = ?
        """, (user_id,))
        
        self.conn.commit()
        logger.info(f"Consent revoked for user {user_id}, recommendations deleted")
    
    def require_consent(self, user_id: str) -> None:
        """Require active consent before proceeding.
        
        Args:
            user_id: User identifier
            
        Raises:
            ConsentError: If user does not have active consent
        """
        if not self.check_consent(user_id):
            raise ConsentError(
                f"User {user_id} has not provided consent. "
                "Explicit opt-in required before processing data or generating recommendations."
            )

