"""Feedback review and analysis for operators"""

from typing import Dict, List, Optional
import sqlite3

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class FeedbackReviewer:
    """Provides feedback review and analysis for operators"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize feedback reviewer.
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
    
    def get_feedback_aggregates(
        self,
        persona_name: Optional[str] = None,
        recommendation_type: Optional[str] = None
    ) -> Dict[str, any]:
        """Get aggregated feedback statistics.
        
        Args:
            persona_name: Filter by persona name (optional)
            recommendation_type: Filter by type ('education' or 'offer')
            
        Returns:
            Dictionary with aggregated feedback statistics
        """
        cursor = self.conn.cursor()
        
        query = """
            SELECT 
                r.type,
                r.persona_name,
                COUNT(f.feedback_id) as total_feedback,
                SUM(CASE WHEN f.thumbs_up = 1 THEN 1 ELSE 0 END) as thumbs_up,
                SUM(CASE WHEN f.thumbs_up = 0 THEN 1 ELSE 0 END) as thumbs_down,
                SUM(CASE WHEN f.helped_me = 1 THEN 1 ELSE 0 END) as helped_me,
                SUM(CASE WHEN f.applied_this = 1 THEN 1 ELSE 0 END) as applied_this
            FROM feedback f
            JOIN recommendations r ON f.recommendation_id = r.recommendation_id
            WHERE 1=1
        """
        params = []
        
        if persona_name:
            query += " AND r.persona_name = ?"
            params.append(persona_name)
        
        if recommendation_type:
            query += " AND r.type = ?"
            params.append(recommendation_type)
        
        query += " GROUP BY r.type, r.persona_name"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        aggregates = []
        for row in results:
            total_thumbs = (row['thumbs_up'] or 0) + (row['thumbs_down'] or 0)
            helpfulness = 0.0
            if total_thumbs > 0:
                helpfulness = ((row['thumbs_up'] or 0) / total_thumbs) * 100
            
            aggregates.append({
                'type': row['type'],
                'persona_name': row['persona_name'],
                'total_feedback': row['total_feedback'],
                'thumbs_up': row['thumbs_up'] or 0,
                'thumbs_down': row['thumbs_down'] or 0,
                'helpfulness_score': round(helpfulness, 2),
                'helped_me': row['helped_me'] or 0,
                'applied_this': row['applied_this'] or 0,
                'action_rate': round(((row['applied_this'] or 0) / row['total_feedback'] * 100) if row['total_feedback'] > 0 else 0, 2)
            })
        
        return aggregates
    
    def get_low_performing_content(
        self,
        min_feedback_count: int = 3,
        max_helpfulness_score: float = 50.0
    ) -> List[Dict[str, any]]:
        """Get low-performing content that needs review.
        
        Args:
            min_feedback_count: Minimum feedback count to consider
            max_helpfulness_score: Maximum helpfulness score to flag as low-performing
            
        Returns:
            List of low-performing recommendation dictionaries
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                r.recommendation_id,
                r.title,
                r.type,
                r.persona_name,
                COUNT(f.feedback_id) as feedback_count,
                SUM(CASE WHEN f.thumbs_up = 1 THEN 1 ELSE 0 END) as thumbs_up,
                SUM(CASE WHEN f.thumbs_up = 0 THEN 1 ELSE 0 END) as thumbs_down
            FROM recommendations r
            LEFT JOIN feedback f ON r.recommendation_id = f.recommendation_id
            GROUP BY r.recommendation_id, r.title, r.type, r.persona_name
            HAVING feedback_count >= ?
        """, (min_feedback_count,))
        
        results = cursor.fetchall()
        
        low_performers = []
        for row in results:
            total_thumbs = (row['thumbs_up'] or 0) + (row['thumbs_down'] or 0)
            if total_thumbs > 0:
                helpfulness = ((row['thumbs_up'] or 0) / total_thumbs) * 100
                
                if helpfulness <= max_helpfulness_score:
                    low_performers.append({
                        'recommendation_id': row['recommendation_id'],
                        'title': row['title'],
                        'type': row['type'],
                        'persona_name': row['persona_name'],
                        'feedback_count': row['feedback_count'],
                        'thumbs_up': row['thumbs_up'] or 0,
                        'thumbs_down': row['thumbs_down'] or 0,
                        'helpfulness_score': round(helpfulness, 2)
                    })
        
        # Sort by helpfulness score (lowest first)
        low_performers.sort(key=lambda x: x['helpfulness_score'])
        
        return low_performers
    
    def get_feedback_by_recommendation(
        self,
        recommendation_id: str
    ) -> List[Dict[str, any]]:
        """Get all feedback for a specific recommendation.
        
        Args:
            recommendation_id: Recommendation identifier
            
        Returns:
            List of feedback dictionaries
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT 
                f.feedback_id,
                f.user_id,
                f.thumbs_up,
                f.helped_me,
                f.applied_this,
                f.already_doing_this,
                f.free_text,
                f.submitted_at
            FROM feedback f
            WHERE f.recommendation_id = ?
            ORDER BY f.submitted_at DESC
        """, (recommendation_id,))
        
        results = cursor.fetchall()
        
        return [
            {
                'feedback_id': row['feedback_id'],
                'user_id': row['user_id'],
                'thumbs_up': row['thumbs_up'],
                'helped_me': row['helped_me'],
                'applied_this': row['applied_this'],
                'already_doing_this': row['already_doing_this'],
                'free_text': row['free_text'],
                'submitted_at': row['submitted_at']
            }
            for row in results
        ]

