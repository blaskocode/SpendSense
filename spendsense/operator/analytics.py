"""Analytics and metrics for operator dashboard"""

from typing import Dict, List
import sqlite3
from datetime import datetime

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class AnalyticsManager:
    """Provides analytics and metrics for operators"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize analytics manager.
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
    
    def get_persona_distribution(self) -> Dict[str, int]:
        """Get persona distribution across all users.
        
        Returns:
            Dictionary mapping persona names to user counts
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT persona_name, COUNT(*) as count
            FROM personas
            GROUP BY persona_name
            ORDER BY count DESC
        """)
        
        results = cursor.fetchall()
        
        return {
            row['persona_name']: row['count']
            for row in results
        }
    
    def get_signal_detection_rates(self) -> Dict[str, any]:
        """Get signal detection rates.
        
        Returns:
            Dictionary with signal detection statistics
        """
        cursor = self.conn.cursor()
        
        # Get total users
        cursor.execute("SELECT COUNT(*) as total FROM users")
        total_users = cursor.fetchone()['total']
        
        # Get users with signals
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) as count
            FROM signals
            WHERE computed_at > datetime('now', '-7 days')
        """)
        users_with_signals = cursor.fetchone()['count']
        
        # Get signal counts by type
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN subscriptions_count > 0 THEN 1 ELSE 0 END) as subscription_signals,
                SUM(CASE WHEN savings_growth_rate > 0 THEN 1 ELSE 0 END) as savings_signals,
                SUM(CASE WHEN credit_utilization > 0 THEN 1 ELSE 0 END) as credit_signals,
                SUM(CASE WHEN income_buffer_months > 0 THEN 1 ELSE 0 END) as income_signals
            FROM signals
            WHERE window_type = '30d'
              AND computed_at > datetime('now', '-7 days')
        """)
        
        signal_counts = cursor.fetchone()
        
        return {
            'total_users': total_users,
            'users_with_signals': users_with_signals,
            'signal_detection_rate': (users_with_signals / total_users * 100) if total_users > 0 else 0,
            'subscription_signals': signal_counts['subscription_signals'] or 0,
            'savings_signals': signal_counts['savings_signals'] or 0,
            'credit_signals': signal_counts['credit_signals'] or 0,
            'income_signals': signal_counts['income_signals'] or 0
        }
    
    def get_recommendation_metrics(self) -> Dict[str, any]:
        """Get recommendation generation metrics.
        
        Returns:
            Dictionary with recommendation statistics
        """
        cursor = self.conn.cursor()
        
        # Total recommendations
        cursor.execute("SELECT COUNT(*) as total FROM recommendations")
        total_recommendations = cursor.fetchone()['total']
        
        # By type
        cursor.execute("""
            SELECT type, COUNT(*) as count
            FROM recommendations
            GROUP BY type
        """)
        by_type = {
            row['type']: row['count']
            for row in cursor.fetchall()
        }
        
        # By operator status
        cursor.execute("""
            SELECT operator_status, COUNT(*) as count
            FROM recommendations
            GROUP BY operator_status
        """)
        by_status = {
            row['operator_status']: row['count']
            for row in cursor.fetchall()
        }
        
        # Average recommendations per user
        cursor.execute("""
            SELECT AVG(count) as avg_per_user
            FROM (
                SELECT user_id, COUNT(*) as count
                FROM recommendations
                GROUP BY user_id
            )
        """)
        avg_per_user = cursor.fetchone()['avg_per_user'] or 0.0
        
        return {
            'total_recommendations': total_recommendations,
            'by_type': by_type,
            'by_status': by_status,
            'avg_per_user': round(avg_per_user, 2)
        }
    
    def get_engagement_metrics(self) -> Dict[str, any]:
        """Get user engagement metrics from feedback.
        
        Returns:
            Dictionary with engagement statistics
        """
        cursor = self.conn.cursor()
        
        # Total feedback submissions
        cursor.execute("SELECT COUNT(*) as total FROM feedback")
        total_feedback = cursor.fetchone()['total']
        
        # Thumbs up/down
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN thumbs_up = 1 THEN 1 ELSE 0 END) as thumbs_up,
                SUM(CASE WHEN thumbs_up = 0 THEN 1 ELSE 0 END) as thumbs_down
            FROM feedback
            WHERE thumbs_up IS NOT NULL
        """)
        thumbs = cursor.fetchone()
        
        thumbs_up = thumbs['thumbs_up'] or 0
        thumbs_down = thumbs['thumbs_down'] or 0
        total_thumbs = thumbs_up + thumbs_down
        
        # Engagement actions
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN helped_me = 1 THEN 1 ELSE 0 END) as helped_me,
                SUM(CASE WHEN applied_this = 1 THEN 1 ELSE 0 END) as applied_this
            FROM feedback
        """)
        actions = cursor.fetchone()
        
        # Users who provided feedback
        cursor.execute("SELECT COUNT(DISTINCT user_id) as count FROM feedback")
        users_with_feedback = cursor.fetchone()['count']
        
        # Total users
        cursor.execute("SELECT COUNT(*) as total FROM users")
        total_users = cursor.fetchone()['total']
        
        # Helpfulness score
        helpfulness_score = 0.0
        if total_thumbs > 0:
            helpfulness_score = (thumbs_up / total_thumbs) * 100
        
        # Engagement rate
        engagement_rate = 0.0
        if total_users > 0:
            engagement_rate = (users_with_feedback / total_users) * 100
        
        return {
            'total_feedback': total_feedback,
            'thumbs_up': thumbs_up,
            'thumbs_down': thumbs_down,
            'helpfulness_score': round(helpfulness_score, 2),
            'helped_me': actions['helped_me'] or 0,
            'applied_this': actions['applied_this'] or 0,
            'users_with_feedback': users_with_feedback,
            'engagement_rate': round(engagement_rate, 2)
        }
    
    def get_coverage_metrics(self) -> Dict[str, any]:
        """Get coverage and explainability metrics.
        
        Returns:
            Dictionary with coverage statistics
        """
        cursor = self.conn.cursor()
        
        # Total users
        cursor.execute("SELECT COUNT(*) as total FROM users")
        total_users = cursor.fetchone()['total']
        
        # Users with persona
        cursor.execute("SELECT COUNT(DISTINCT user_id) as count FROM personas")
        users_with_persona = cursor.fetchone()['count']
        
        # Users with recommendations
        cursor.execute("SELECT COUNT(DISTINCT user_id) as count FROM recommendations")
        users_with_recommendations = cursor.fetchone()['count']
        
        # Recommendations with rationales
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM recommendations
            WHERE rationale IS NOT NULL AND rationale != ''
        """)
        recommendations_with_rationales = cursor.fetchone()['count']
        
        # Total recommendations
        cursor.execute("SELECT COUNT(*) as total FROM recommendations")
        total_recommendations = cursor.fetchone()['total']
        
        # Recommendations with decision traces
        cursor.execute("""
            SELECT COUNT(DISTINCT p.user_id) as count
            FROM personas p
            WHERE p.decision_trace IS NOT NULL AND p.decision_trace != ''
        """)
        users_with_traces = cursor.fetchone()['count']
        
        return {
            'total_users': total_users,
            'users_with_persona': users_with_persona,
            'persona_coverage': round((users_with_persona / total_users * 100) if total_users > 0 else 0, 2),
            'users_with_recommendations': users_with_recommendations,
            'recommendation_coverage': round((users_with_recommendations / total_users * 100) if total_users > 0 else 0, 2),
            'total_recommendations': total_recommendations,
            'recommendations_with_rationales': recommendations_with_rationales,
            'explainability_rate': round((recommendations_with_rationales / total_recommendations * 100) if total_recommendations > 0 else 0, 2),
            'users_with_traces': users_with_traces,
            'auditability_rate': round((users_with_traces / total_users * 100) if total_users > 0 else 0, 2)
        }
    
    def get_all_analytics(self) -> Dict[str, any]:
        """Get all analytics in one call.
        
        Returns:
            Dictionary with all analytics
        """
        return {
            'persona_distribution': self.get_persona_distribution(),
            'signal_detection': self.get_signal_detection_rates(),
            'recommendations': self.get_recommendation_metrics(),
            'engagement': self.get_engagement_metrics(),
            'coverage': self.get_coverage_metrics(),
            'generated_at': datetime.now().isoformat()
        }

