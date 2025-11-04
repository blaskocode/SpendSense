"""Automatic scoring system for evaluation"""

import sqlite3
import time
from typing import Dict, List, Optional
from datetime import datetime

from ..utils.logger import setup_logger
from ..features.aggregator import SignalAggregator
from ..personas.assignment import PersonaAssigner
from ..recommend.engine import RecommendationEngine

logger = setup_logger(__name__)


class ScoringSystem:
    """Computes automatic scoring metrics for system evaluation"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize scoring system.
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
        self.signal_aggregator = SignalAggregator(db_connection)
        self.persona_assigner = PersonaAssigner(db_connection)
        self.recommendation_engine = RecommendationEngine(db_connection)
    
    def compute_coverage_score(self) -> Dict[str, any]:
        """Compute coverage score: % users with persona + ≥3 behaviors.
        
        Target: 100%
        
        Returns:
            Dictionary with coverage metrics
        """
        cursor = self.conn.cursor()
        
        # Total users
        cursor.execute("SELECT COUNT(*) as total FROM users")
        total_users = cursor.fetchone()['total']
        
        # Users with persona
        cursor.execute("SELECT COUNT(DISTINCT user_id) as count FROM personas")
        users_with_persona = cursor.fetchone()['count']
        
        # Users with ≥3 behaviors detected
        cursor.execute("""
            SELECT DISTINCT user_id
            FROM signals
            WHERE window_type = '30d'
            GROUP BY user_id
            HAVING 
                SUM(CASE WHEN subscriptions_count > 0 THEN 1 ELSE 0 END) +
                SUM(CASE WHEN savings_growth_rate > 0 OR savings_growth_rate < 0 THEN 1 ELSE 0 END) +
                SUM(CASE WHEN credit_utilization > 0 THEN 1 ELSE 0 END) +
                SUM(CASE WHEN income_buffer_months > 0 OR income_buffer_months < 0 THEN 1 ELSE 0 END) >= 3
        """)
        users_with_3_behaviors = len(cursor.fetchall())
        
        # Users with both persona and ≥3 behaviors
        cursor.execute("""
            SELECT DISTINCT p.user_id
            FROM personas p
            JOIN signals s ON p.user_id = s.user_id
            WHERE s.window_type = '30d'
            GROUP BY p.user_id
            HAVING 
                SUM(CASE WHEN s.subscriptions_count > 0 THEN 1 ELSE 0 END) +
                SUM(CASE WHEN s.savings_growth_rate > 0 OR s.savings_growth_rate < 0 THEN 1 ELSE 0 END) +
                SUM(CASE WHEN s.credit_utilization > 0 THEN 1 ELSE 0 END) +
                SUM(CASE WHEN s.income_buffer_months > 0 OR s.income_buffer_months < 0 THEN 1 ELSE 0 END) >= 3
        """)
        users_with_persona_and_behaviors = len(cursor.fetchall())
        
        coverage_rate = (users_with_persona_and_behaviors / total_users * 100) if total_users > 0 else 0
        
        return {
            'total_users': total_users,
            'users_with_persona': users_with_persona,
            'users_with_3_behaviors': users_with_3_behaviors,
            'users_with_persona_and_behaviors': users_with_persona_and_behaviors,
            'coverage_rate': round(coverage_rate, 2),
            'target': 100.0,
            'meets_target': coverage_rate >= 100.0
        }
    
    def compute_explainability_score(self) -> Dict[str, any]:
        """Compute explainability score: % recommendations with rationales.
        
        Target: 100%
        
        Returns:
            Dictionary with explainability metrics
        """
        cursor = self.conn.cursor()
        
        # Total recommendations
        cursor.execute("SELECT COUNT(*) as total FROM recommendations")
        total_recommendations = cursor.fetchone()['total']
        
        # Recommendations with rationales
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM recommendations
            WHERE rationale IS NOT NULL AND rationale != ''
        """)
        recommendations_with_rationales = cursor.fetchone()['count']
        
        explainability_rate = (recommendations_with_rationales / total_recommendations * 100) if total_recommendations > 0 else 0
        
        return {
            'total_recommendations': total_recommendations,
            'recommendations_with_rationales': recommendations_with_rationales,
            'explainability_rate': round(explainability_rate, 2),
            'target': 100.0,
            'meets_target': explainability_rate >= 100.0
        }
    
    def compute_latency_score(self, sample_size: int = 10) -> Dict[str, any]:
        """Compute latency score: time to generate recommendations per user.
        
        Target: <5 seconds per user
        
        Args:
            sample_size: Number of users to test (default: 10)
            
        Returns:
            Dictionary with latency metrics
        """
        cursor = self.conn.cursor()
        
        # Get sample users with consent
        cursor.execute("""
            SELECT DISTINCT u.user_id
            FROM users u
            WHERE u.consent_status = 1
            LIMIT ?
        """, (sample_size,))
        
        sample_users = [row['user_id'] for row in cursor.fetchall()]
        
        if not sample_users:
            return {
                'sample_size': 0,
                'avg_latency_seconds': 0.0,
                'max_latency_seconds': 0.0,
                'min_latency_seconds': 0.0,
                'target': 5.0,
                'meets_target': False
            }
        
        latencies = []
        
        for user_id in sample_users:
            try:
                start_time = time.time()
                
                # Generate recommendations (this includes all steps)
                self.recommendation_engine.generate_and_save(user_id)
                
                elapsed = time.time() - start_time
                latencies.append(elapsed)
                
            except Exception as e:
                logger.warning(f"Error computing latency for {user_id}: {e}")
                continue
        
        if not latencies:
            return {
                'sample_size': len(sample_users),
                'avg_latency_seconds': 0.0,
                'max_latency_seconds': 0.0,
                'min_latency_seconds': 0.0,
                'target': 5.0,
                'meets_target': False
            }
        
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)
        
        return {
            'sample_size': len(sample_users),
            'avg_latency_seconds': round(avg_latency, 2),
            'max_latency_seconds': round(max_latency, 2),
            'min_latency_seconds': round(min_latency, 2),
            'target': 5.0,
            'meets_target': avg_latency < 5.0
        }
    
    def compute_auditability_score(self) -> Dict[str, any]:
        """Compute auditability score: % users with decision traces.
        
        Target: 100%
        
        Returns:
            Dictionary with auditability metrics
        """
        cursor = self.conn.cursor()
        
        # Total users
        cursor.execute("SELECT COUNT(*) as total FROM users")
        total_users = cursor.fetchone()['total']
        
        # Users with decision traces
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) as count
            FROM personas
            WHERE decision_trace IS NOT NULL AND decision_trace != ''
        """)
        users_with_traces = cursor.fetchone()['count']
        
        auditability_rate = (users_with_traces / total_users * 100) if total_users > 0 else 0
        
        return {
            'total_users': total_users,
            'users_with_traces': users_with_traces,
            'auditability_rate': round(auditability_rate, 2),
            'target': 100.0,
            'meets_target': auditability_rate >= 100.0
        }
    
    def compute_relevance_score(self) -> Dict[str, any]:
        """Compute relevance score: rules-based scoring of education-persona fit.
        
        Returns:
            Dictionary with relevance metrics
        """
        cursor = self.conn.cursor()
        
        # Get all recommendations with persona assignments
        cursor.execute("""
            SELECT r.recommendation_id, r.type, r.persona_name, p.persona_name as assigned_persona
            FROM recommendations r
            LEFT JOIN personas p ON r.user_id = p.user_id
            WHERE r.type = 'education'
        """)
        
        recommendations = cursor.fetchall()
        
        if not recommendations:
            return {
                'total_education_recommendations': 0,
                'matching_persona': 0,
                'relevance_rate': 0.0
            }
        
        matching = sum(1 for rec in recommendations if rec['persona_name'] == rec['assigned_persona'])
        relevance_rate = (matching / len(recommendations) * 100) if recommendations else 0
        
        return {
            'total_education_recommendations': len(recommendations),
            'matching_persona': matching,
            'relevance_rate': round(relevance_rate, 2)
        }
    
    def compute_all_scores(self, latency_sample_size: int = 10) -> Dict[str, any]:
        """Compute all automatic scores.
        
        Args:
            latency_sample_size: Number of users to test for latency (default: 10)
            
        Returns:
            Dictionary with all scores
        """
        logger.info("Computing automatic scores...")
        
        return {
            'coverage': self.compute_coverage_score(),
            'explainability': self.compute_explainability_score(),
            'latency': self.compute_latency_score(latency_sample_size),
            'auditability': self.compute_auditability_score(),
            'relevance': self.compute_relevance_score(),
            'computed_at': datetime.now().isoformat()
        }

