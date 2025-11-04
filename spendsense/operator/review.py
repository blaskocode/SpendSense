"""User review functionality for operators"""

from typing import List, Dict, Optional
import sqlite3
import json

from ..personas.assignment import PersonaAssigner
from ..features.aggregator import SignalAggregator
from ..features.degradation import GracefulDegradation
from ..recommend.engine import RecommendationEngine
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class UserReviewer:
    """Provides user review functionality for operators"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize user reviewer.
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
        self.aggregator = SignalAggregator(db_connection)
        self.degradation = GracefulDegradation(self.aggregator)
        self.persona_assigner = PersonaAssigner(db_connection)
        self.recommendation_engine = RecommendationEngine(db_connection)
    
    def get_user_profile(
        self,
        user_id: str
    ) -> Dict[str, any]:
        """Get complete user profile for review.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with complete user profile including:
            - user_id, signals (30d and 180d), persona, recommendations, decision_trace
        """
        cursor = self.conn.cursor()
        
        # Get user info
        cursor.execute("""
            SELECT user_id, created_at, consent_status, consent_timestamp, last_updated
            FROM users
            WHERE user_id = ?
        """, (user_id,))
        
        user_row = cursor.fetchone()
        if not user_row:
            return {}
        
        # Get signals for both windows
        signals_30d = None
        signals_180d = None
        
        try:
            signals_30d = self.aggregator.compute_signals(user_id, '30d', use_cache=True)
            signals_180d = self.aggregator.compute_signals(user_id, '180d', use_cache=True)
        except Exception as e:
            logger.warning(f"Error computing signals for user {user_id}: {e}")
        
        # Get persona assignment
        assignment = self.persona_assigner.get_assignment(user_id)
        if not assignment:
            assignment = self.persona_assigner.assign_and_save(user_id)
        
        # Get all matching personas (from decision trace)
        decision_trace = {}
        all_matched_personas = []
        if assignment.get('decision_trace'):
            try:
                decision_trace = json.loads(assignment['decision_trace']) if isinstance(assignment['decision_trace'], str) else assignment['decision_trace']
                all_matched_personas = decision_trace.get('all_matched_personas', [])
            except:
                decision_trace = {}
        
        # Get recommendations
        recommendations = self.recommendation_engine.get_recommendations(user_id)
        
        # Get data availability
        data_availability = self.degradation.get_signals_with_degradation(user_id).get('data_availability', 'unknown')
        
        return {
            'user_id': user_row['user_id'],
            'created_at': user_row['created_at'],
            'consent_status': bool(user_row['consent_status']),
            'consent_timestamp': user_row['consent_timestamp'],
            'last_updated': user_row['last_updated'],
            'data_availability': data_availability,
            'signals_30d': signals_30d,
            'signals_180d': signals_180d,
            'persona': {
                'persona_name': assignment.get('persona_name'),
                'priority_level': assignment.get('priority_level'),
                'signal_strength': assignment.get('signal_strength'),
                'all_matched_personas': all_matched_personas,
                'decision_trace': decision_trace
            },
            'recommendations': recommendations,
            'recommendation_count': len(recommendations)
        }
    
    def search_users(
        self,
        user_id_pattern: Optional[str] = None,
        persona_name: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, any]]:
        """Search users with optional filters.
        
        Args:
            user_id_pattern: User ID pattern to search (partial match)
            persona_name: Filter by persona name
            limit: Maximum number of results
            
        Returns:
            List of user summary dictionaries
        """
        cursor = self.conn.cursor()
        
        query = """
            SELECT DISTINCT u.user_id, u.created_at, u.consent_status,
                   p.persona_name, p.priority_level, p.signal_strength
            FROM users u
            LEFT JOIN personas p ON u.user_id = p.user_id
            WHERE 1=1
        """
        params = []
        
        if user_id_pattern:
            query += " AND u.user_id LIKE ?"
            params.append(f"%{user_id_pattern}%")
        
        if persona_name:
            query += " AND p.persona_name = ?"
            params.append(persona_name)
        
        query += " ORDER BY u.user_id LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        return [
            {
                'user_id': row['user_id'],
                'created_at': row['created_at'],
                'consent_status': bool(row['consent_status']),
                'persona_name': row['persona_name'],
                'priority_level': row['priority_level'],
                'signal_strength': row['signal_strength']
            }
            for row in results
        ]

