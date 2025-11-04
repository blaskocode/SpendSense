"""Feedback collection system"""

from typing import Optional
from datetime import datetime
import sqlite3
import uuid

from ..utils.logger import setup_logger
from ..utils.errors import DataError

logger = setup_logger(__name__)


class FeedbackCollector:
    """Collects and stores user feedback on recommendations"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize feedback collector.
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
    
    def submit_feedback(
        self,
        recommendation_id: str,
        user_id: str,
        thumbs_up: Optional[bool] = None,
        helped_me: Optional[bool] = None,
        applied_this: Optional[bool] = None,
        free_text: Optional[str] = None
    ) -> str:
        """Submit feedback for a recommendation.
        
        Args:
            recommendation_id: Recommendation identifier
            user_id: User identifier
            thumbs_up: Thumbs up/down (True = up, False = down)
            helped_me: "This helped me" flag
            applied_this: "I applied this" flag
            free_text: Optional free-text feedback (<200 chars)
            
        Returns:
            Feedback ID
            
        Raises:
            DataError: If recommendation not found or free_text too long
        """
        # Validate free text length
        if free_text and len(free_text) > 200:
            raise DataError("Free text feedback must be 200 characters or less")
        
        # Verify recommendation exists
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT recommendation_id FROM recommendations
            WHERE recommendation_id = ? AND user_id = ?
        """, (recommendation_id, user_id))
        
        if not cursor.fetchone():
            raise DataError(f"Recommendation {recommendation_id} not found for user {user_id}")
        
        # Create feedback record
        feedback_id = str(uuid.uuid4())
        submitted_at = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO feedback (
                feedback_id, recommendation_id, user_id,
                thumbs_up, helped_me, applied_this,
                free_text, submitted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            feedback_id,
            recommendation_id,
            user_id,
            thumbs_up,
            helped_me,
            applied_this,
            free_text,
            submitted_at
        ))
        
        self.conn.commit()
        logger.info(
            f"Feedback submitted for recommendation {recommendation_id} "
            f"by user {user_id}"
        )
        
        return feedback_id
    
    def get_feedback(self, recommendation_id: str) -> list:
        """Get all feedback for a recommendation.
        
        Args:
            recommendation_id: Recommendation identifier
            
        Returns:
            List of feedback dictionaries
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT feedback_id, user_id, thumbs_up, helped_me,
                   applied_this, free_text, submitted_at
            FROM feedback
            WHERE recommendation_id = ?
            ORDER BY submitted_at DESC
        """, (recommendation_id,))
        
        results = cursor.fetchall()
        
        return [
            {
                'feedback_id': row['feedback_id'],
                'user_id': row['user_id'],
                'thumbs_up': row['thumbs_up'],
                'helped_me': row['helped_me'],
                'applied_this': row['applied_this'],
                'free_text': row['free_text'],
                'submitted_at': row['submitted_at']
            }
            for row in results
        ]
    
    def get_user_feedback(self, user_id: str) -> list:
        """Get all feedback submitted by a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of feedback dictionaries
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT f.feedback_id, f.recommendation_id, f.thumbs_up,
                   f.helped_me, f.applied_this, f.free_text, f.submitted_at,
                   r.title, r.type
            FROM feedback f
            JOIN recommendations r ON f.recommendation_id = r.recommendation_id
            WHERE f.user_id = ?
            ORDER BY f.submitted_at DESC
        """, (user_id,))
        
        results = cursor.fetchall()
        
        return [
            {
                'feedback_id': row['feedback_id'],
                'recommendation_id': row['recommendation_id'],
                'recommendation_title': row['title'],
                'recommendation_type': row['type'],
                'thumbs_up': row['thumbs_up'],
                'helped_me': row['helped_me'],
                'applied_this': row['applied_this'],
                'free_text': row['free_text'],
                'submitted_at': row['submitted_at']
            }
            for row in results
        ]

