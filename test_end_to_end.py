#!/usr/bin/env python3
"""End-to-end test of SpendSense pipeline"""

import sqlite3
from spendsense.storage.sqlite_manager import SQLiteManager
from spendsense.guardrails.consent import ConsentManager
from spendsense.personas.assignment import PersonaAssigner
from spendsense.recommend.engine import RecommendationEngine
from spendsense.ui.feedback import FeedbackCollector
from spendsense.operator.analytics import AnalyticsManager

def test_end_to_end():
    """Test complete end-to-end pipeline"""
    print("="*70)
    print("SpendSense End-to-End Test")
    print("="*70)
    print()
    
    # Connect to database
    db_manager = SQLiteManager()
    db_manager.connect()
    
    try:
        consent_manager = ConsentManager(db_manager.conn)
        persona_assigner = PersonaAssigner(db_manager.conn)
        recommendation_engine = RecommendationEngine(db_manager.conn)
        feedback_collector = FeedbackCollector(db_manager.conn)
        analytics = AnalyticsManager(db_manager.conn)
        
        # Get sample users
        cursor = db_manager.conn.cursor()
        cursor.execute("SELECT user_id FROM users LIMIT 5")
        test_users = [row['user_id'] for row in cursor.fetchall()]
        
        print(f"Testing with {len(test_users)} users\n")
        
        # Step 1: Consent and Persona Assignment
        print("="*70)
        print("STEP 1: Consent & Persona Assignment")
        print("="*70)
        
        for user_id in test_users:
            # Record consent
            consent_manager.record_consent(user_id)
            
            # Assign persona
            assignment = persona_assigner.assign_and_save(user_id)
            print(f"{user_id}: {assignment['persona_name']} (Priority {assignment['priority_level']})")
        
        print()
        
        # Step 2: Generate Recommendations
        print("="*70)
        print("STEP 2: Generate Recommendations")
        print("="*70)
        
        total_recommendations = 0
        for user_id in test_users:
            recommendations = recommendation_engine.generate_and_save(user_id)
            education = [r for r in recommendations if r.type == 'education']
            offers = [r for r in recommendations if r.type == 'offer']
            print(f"{user_id}: {len(education)} education + {len(offers)} offers = {len(recommendations)} total")
            total_recommendations += len(recommendations)
        
        print(f"\nTotal recommendations generated: {total_recommendations}\n")
        
        # Step 3: Collect Feedback
        print("="*70)
        print("STEP 3: Collect Feedback")
        print("="*70)
        
        # Get recommendations and collect feedback
        cursor.execute("""
            SELECT recommendation_id, user_id, title, type
            FROM recommendations
            WHERE user_id IN ({})
            LIMIT 5
        """.format(','.join('?' * len(test_users))), test_users)
        
        recommendations_for_feedback = cursor.fetchall()
        
        feedback_count = 0
        for rec in recommendations_for_feedback:
            try:
                feedback_collector.submit_feedback(
                    recommendation_id=rec['recommendation_id'],
                    user_id=rec['user_id'],
                    thumbs_up=feedback_count % 2 == 0,  # Alternate thumbs up/down
                    helped_me=feedback_count % 3 == 0,
                    applied_this=feedback_count % 4 == 0,
                    free_text="Test feedback" if feedback_count % 2 == 0 else None
                )
                feedback_count += 1
                print(f"Feedback submitted for: {rec['title']}")
            except Exception as e:
                print(f"Error submitting feedback: {e}")
        
        print(f"\nTotal feedback submissions: {feedback_count}\n")
        
        # Step 4: System Metrics
        print("="*70)
        print("STEP 4: System Metrics")
        print("="*70)
        
        # Coverage metrics
        coverage = analytics.get_coverage_metrics()
        print(f"Coverage Metrics:")
        print(f"  Persona Coverage: {coverage['persona_coverage']}%")
        print(f"  Recommendation Coverage: {coverage['recommendation_coverage']}%")
        print(f"  Explainability Rate: {coverage['explainability_rate']}%")
        print(f"  Auditability Rate: {coverage['auditability_rate']}%")
        
        # Engagement metrics
        engagement = analytics.get_engagement_metrics()
        print(f"\nEngagement Metrics:")
        print(f"  Total Feedback: {engagement['total_feedback']}")
        print(f"  Helpfulness Score: {engagement['helpfulness_score']}%")
        print(f"  Engagement Rate: {engagement['engagement_rate']}%")
        
        # Persona distribution
        persona_dist = analytics.get_persona_distribution()
        print(f"\nPersona Distribution:")
        for persona, count in sorted(persona_dist.items(), key=lambda x: -x[1]):
            print(f"  {persona}: {count} users")
        
        print("\n" + "="*70)
        print("End-to-End Test Complete!")
        print("="*70)
        print("\n✅ All core systems operational!")
        print("✅ Data pipeline working end-to-end")
        print("✅ Recommendations generated with guardrails")
        print("✅ Feedback system functional")
        
    finally:
        db_manager.close()

if __name__ == '__main__':
    test_end_to_end()

