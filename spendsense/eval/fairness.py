"""Fairness analysis (behavior-based, no demographics)"""

import sqlite3
import json
from typing import Dict, List, Tuple
from datetime import datetime

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class FairnessAnalyzer:
    """Analyzes fairness across income levels and account complexity"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize fairness analyzer.
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
    
    def detect_income_quartiles(self) -> Dict[str, List[str]]:
        """Detect income quartiles from payroll amounts.
        
        Returns:
            Dictionary mapping quartile names to lists of user IDs
        """
        cursor = self.conn.cursor()
        
        # Get average monthly payroll amounts per user
        # Need to join through accounts to get user_id
        cursor.execute("""
            SELECT 
                a.user_id,
                AVG(t.amount) as avg_payroll_amount
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE t.amount > 0
              AND (t.merchant_name LIKE '%payroll%' 
                   OR t.merchant_name LIKE '%ach%'
                   OR t.payment_channel LIKE '%ach%'
                   OR t.amount > 500)
              AND t.pending = 0
            GROUP BY a.user_id
            HAVING COUNT(*) >= 2
            ORDER BY avg_payroll_amount
        """)
        
        users_with_income = cursor.fetchall()
        
        if not users_with_income:
            return {
                'q1': [],
                'q2': [],
                'q3': [],
                'q4': []
            }
        
        total = len(users_with_income)
        q1_end = total // 4
        q2_end = total // 2
        q3_end = 3 * total // 4
        
        return {
            'q1': [row['user_id'] for row in users_with_income[:q1_end]],
            'q2': [row['user_id'] for row in users_with_income[q1_end:q2_end]],
            'q3': [row['user_id'] for row in users_with_income[q2_end:q3_end]],
            'q4': [row['user_id'] for row in users_with_income[q3_end:]]
        }
    
    def analyze_persona_distribution_by_income(self) -> Dict[str, any]:
        """Analyze persona distribution across income quartiles.
        
        Returns:
            Dictionary with persona distribution by income level
        """
        quartiles = self.detect_income_quartiles()
        
        cursor = self.conn.cursor()
        
        distribution = {}
        
        for quartile_name, user_ids in quartiles.items():
            if not user_ids:
                distribution[quartile_name] = {}
                continue
            
            placeholders = ','.join('?' * len(user_ids))
            cursor.execute(f"""
                SELECT persona_name, COUNT(*) as count
                FROM personas
                WHERE user_id IN ({placeholders})
                GROUP BY persona_name
            """, user_ids)
            
            persona_counts = {
                row['persona_name']: row['count']
                for row in cursor.fetchall()
            }
            
            distribution[quartile_name] = {
                'total_users': len(user_ids),
                'persona_distribution': persona_counts
            }
        
        return distribution
    
    def analyze_recommendation_count_by_income(self) -> Dict[str, any]:
        """Analyze average recommendation count by income level.
        
        Returns:
            Dictionary with recommendation counts by income quartile
        """
        quartiles = self.detect_income_quartiles()
        
        cursor = self.conn.cursor()
        
        results = {}
        
        for quartile_name, user_ids in quartiles.items():
            if not user_ids:
                results[quartile_name] = {
                    'total_users': 0,
                    'avg_recommendations': 0.0,
                    'total_recommendations': 0
                }
                continue
            
            placeholders = ','.join('?' * len(user_ids))
            cursor.execute(f"""
                SELECT 
                    COUNT(DISTINCT user_id) as total_users,
                    AVG(rec_count) as avg_recommendations,
                    SUM(rec_count) as total_recommendations
                FROM (
                    SELECT user_id, COUNT(*) as rec_count
                    FROM recommendations
                    WHERE user_id IN ({placeholders})
                    GROUP BY user_id
                )
            """, user_ids)
            
            result = cursor.fetchone()
            
            results[quartile_name] = {
                'total_users': result['total_users'] or 0,
                'avg_recommendations': round(result['avg_recommendations'] or 0.0, 2),
                'total_recommendations': result['total_recommendations'] or 0
            }
        
        return results
    
    def analyze_offer_eligibility_by_complexity(self) -> Dict[str, any]:
        """Analyze offer eligibility rates by account complexity.
        
        Returns:
            Dictionary with offer eligibility by account complexity
        """
        cursor = self.conn.cursor()
        
        # Classify users by account complexity
        cursor.execute("""
            SELECT 
                u.user_id,
                COUNT(DISTINCT a.account_id) as account_count,
                SUM(CASE WHEN a.type IN ('checking', 'savings') THEN 1 ELSE 0 END) as deposit_accounts,
                SUM(CASE WHEN a.type = 'credit_card' THEN 1 ELSE 0 END) as credit_accounts
            FROM users u
            LEFT JOIN accounts a ON u.user_id = a.user_id
            GROUP BY u.user_id
        """)
        
        users_complexity = cursor.fetchall()
        
        # Classify into basic (1-2 accounts) vs full suite (3+ accounts)
        basic_users = []
        full_suite_users = []
        
        for user in users_complexity:
            total_accounts = user['account_count'] or 0
            if total_accounts <= 2:
                basic_users.append(user['user_id'])
            else:
                full_suite_users.append(user['user_id'])
        
        # Analyze offer eligibility
        results = {}
        
        for category, user_ids in [('basic', basic_users), ('full_suite', full_suite_users)]:
            if not user_ids:
                results[category] = {
                    'total_users': 0,
                    'users_with_offers': 0,
                    'eligibility_rate': 0.0
                }
                continue
            
            placeholders = ','.join('?' * len(user_ids))
            cursor.execute(f"""
                SELECT COUNT(DISTINCT user_id) as users_with_offers
                FROM recommendations
                WHERE user_id IN ({placeholders})
                  AND type = 'offer'
            """, user_ids)
            
            users_with_offers = cursor.fetchone()['users_with_offers'] or 0
            eligibility_rate = (users_with_offers / len(user_ids) * 100) if user_ids else 0
            
            results[category] = {
                'total_users': len(user_ids),
                'users_with_offers': users_with_offers,
                'eligibility_rate': round(eligibility_rate, 2)
            }
        
        return results
    
    def analyze_tone_sentiment_by_persona(self) -> Dict[str, any]:
        """Analyze tone sentiment across personas.
        
        Note: This is a simplified analysis - in production, would use NLP.
        
        Returns:
            Dictionary with tone analysis by persona
        """
        cursor = self.conn.cursor()
        
        # Get recommendations by persona
        cursor.execute("""
            SELECT 
                p.persona_name,
                COUNT(*) as total_recommendations,
                SUM(CASE WHEN r.rationale LIKE '%help%' OR r.rationale LIKE '%support%' THEN 1 ELSE 0 END) as positive_keywords,
                SUM(CASE WHEN r.rationale LIKE '%because%' THEN 1 ELSE 0 END) as explanatory_keywords
            FROM recommendations r
            JOIN personas p ON r.user_id = p.user_id
            GROUP BY p.persona_name
        """)
        
        results = {}
        for row in cursor.fetchall():
            total = row['total_recommendations']
            positive_rate = (row['positive_keywords'] / total * 100) if total > 0 else 0
            explanatory_rate = (row['explanatory_keywords'] / total * 100) if total > 0 else 0
            
            results[row['persona_name']] = {
                'total_recommendations': total,
                'positive_keyword_rate': round(positive_rate, 2),
                'explanatory_keyword_rate': round(explanatory_rate, 2)
            }
        
        return results
    
    def detect_systematic_bias(self) -> Dict[str, any]:
        """Detect systematic bias (e.g., low-income excluded).
        
        Returns:
            Dictionary with bias detection results
        """
        # Analyze persona distribution by income
        persona_dist = self.analyze_persona_distribution_by_income()
        
        # Analyze recommendation counts by income
        rec_counts = self.analyze_recommendation_count_by_income()
        
        # Check if Q1 (lowest income) has significantly lower coverage
        q1_avg_recs = rec_counts.get('q1', {}).get('avg_recommendations', 0)
        q4_avg_recs = rec_counts.get('q4', {}).get('avg_recommendations', 0)
        
        # Calculate ratio
        ratio = (q1_avg_recs / q4_avg_recs) if q4_avg_recs > 0 else 0
        
        # Flag if Q1 gets < 50% of Q4 recommendations
        bias_detected = ratio < 0.5 if ratio > 0 else False
        
        # Check persona coverage
        q1_personas = persona_dist.get('q1', {}).get('total_users', 0)
        q4_personas = persona_dist.get('q4', {}).get('total_users', 0)
        q1_total = len(self.detect_income_quartiles()['q1'])
        q4_total = len(self.detect_income_quartiles()['q4'])
        
        q1_coverage = (q1_personas / q1_total * 100) if q1_total > 0 else 0
        q4_coverage = (q4_personas / q4_total * 100) if q4_total > 0 else 0
        
        coverage_bias = (q1_coverage < 50) and (q4_coverage > q1_coverage * 1.5)
        
        return {
            'recommendation_ratio_q1_to_q4': round(ratio, 2),
            'bias_detected_recommendations': bias_detected,
            'q1_coverage_rate': round(q1_coverage, 2),
            'q4_coverage_rate': round(q4_coverage, 2),
            'bias_detected_coverage': coverage_bias,
            'overall_bias_detected': bias_detected or coverage_bias
        }
    
    def compute_all_fairness_metrics(self) -> Dict[str, any]:
        """Compute all fairness metrics.
        
        Returns:
            Dictionary with all fairness analysis results
        """
        logger.info("Computing fairness metrics...")
        
        return {
            'income_quartiles': self.detect_income_quartiles(),
            'persona_distribution_by_income': self.analyze_persona_distribution_by_income(),
            'recommendation_count_by_income': self.analyze_recommendation_count_by_income(),
            'offer_eligibility_by_complexity': self.analyze_offer_eligibility_by_complexity(),
            'tone_sentiment_by_persona': self.analyze_tone_sentiment_by_persona(),
            'bias_detection': self.detect_systematic_bias(),
            'computed_at': datetime.now().isoformat()
        }

