"""User satisfaction metrics from feedback"""

import sqlite3
from typing import Dict, List
from datetime import datetime

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class SatisfactionMetrics:
    """Computes user satisfaction metrics from feedback"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize satisfaction metrics calculator.
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
    
    def compute_engagement_rate(self) -> Dict[str, any]:
        """Compute engagement rate: % recommendations interacted with.
        
        Returns:
            Dictionary with engagement metrics
        """
        cursor = self.conn.cursor()
        
        # Total recommendations
        cursor.execute("SELECT COUNT(*) as total FROM recommendations")
        total_recommendations = cursor.fetchone()['total']
        
        # Recommendations with feedback
        cursor.execute("""
            SELECT COUNT(DISTINCT recommendation_id) as count
            FROM feedback
        """)
        recommendations_with_feedback = cursor.fetchone()['count']
        
        engagement_rate = (recommendations_with_feedback / total_recommendations * 100) if total_recommendations > 0 else 0
        
        # Users who provided feedback
        cursor.execute("SELECT COUNT(DISTINCT user_id) as count FROM feedback")
        users_with_feedback = cursor.fetchone()['count']
        
        # Total users
        cursor.execute("SELECT COUNT(*) as total FROM users")
        total_users = cursor.fetchone()['total']
        
        user_engagement_rate = (users_with_feedback / total_users * 100) if total_users > 0 else 0
        
        return {
            'total_recommendations': total_recommendations,
            'recommendations_with_feedback': recommendations_with_feedback,
            'engagement_rate': round(engagement_rate, 2),
            'users_with_feedback': users_with_feedback,
            'total_users': total_users,
            'user_engagement_rate': round(user_engagement_rate, 2)
        }
    
    def compute_helpfulness_score(self) -> Dict[str, any]:
        """Compute helpfulness score: thumbs up / (thumbs up + thumbs down).
        
        Returns:
            Dictionary with helpfulness metrics
        """
        cursor = self.conn.cursor()
        
        # Thumbs up/down
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN thumbs_up = 1 THEN 1 ELSE 0 END) as thumbs_up,
                SUM(CASE WHEN thumbs_up = 0 THEN 1 ELSE 0 END) as thumbs_down
            FROM feedback
            WHERE thumbs_up IS NOT NULL
        """)
        
        result = cursor.fetchone()
        thumbs_up = result['thumbs_up'] or 0
        thumbs_down = result['thumbs_down'] or 0
        total_thumbs = thumbs_up + thumbs_down
        
        helpfulness_score = (thumbs_up / total_thumbs * 100) if total_thumbs > 0 else 0
        
        return {
            'thumbs_up': thumbs_up,
            'thumbs_down': thumbs_down,
            'total_thumbs': total_thumbs,
            'helpfulness_score': round(helpfulness_score, 2)
        }
    
    def compute_action_rate(self) -> Dict[str, any]:
        """Compute action rate: % marked "I applied this".
        
        Returns:
            Dictionary with action metrics
        """
        cursor = self.conn.cursor()
        
        # Total feedback submissions
        cursor.execute("SELECT COUNT(*) as total FROM feedback")
        total_feedback = cursor.fetchone()['total']
        
        # Feedback with "applied this"
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM feedback
            WHERE applied_this = 1
        """)
        applied_this_count = cursor.fetchone()['count']
        
        action_rate = (applied_this_count / total_feedback * 100) if total_feedback > 0 else 0
        
        # Also get "helped me" count
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM feedback
            WHERE helped_me = 1
        """)
        helped_me_count = cursor.fetchone()['count']
        
        helped_rate = (helped_me_count / total_feedback * 100) if total_feedback > 0 else 0
        
        return {
            'total_feedback': total_feedback,
            'applied_this_count': applied_this_count,
            'action_rate': round(action_rate, 2),
            'helped_me_count': helped_me_count,
            'helped_rate': round(helped_rate, 2)
        }
    
    def compute_all_satisfaction_metrics(self) -> Dict[str, any]:
        """Compute all user satisfaction metrics.
        
        Returns:
            Dictionary with all satisfaction metrics
        """
        logger.info("Computing user satisfaction metrics...")
        
        return {
            'engagement': self.compute_engagement_rate(),
            'helpfulness': self.compute_helpfulness_score(),
            'action': self.compute_action_rate(),
            'computed_at': datetime.now().isoformat()
        }

