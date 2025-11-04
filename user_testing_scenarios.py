#!/usr/bin/env python3
"""User testing scenarios for SpendSense"""

import sys
from spendsense.storage.sqlite_manager import SQLiteManager
from spendsense.guardrails.consent import ConsentManager
from spendsense.personas.assignment import PersonaAssigner
from spendsense.recommend.engine import RecommendationEngine
from spendsense.ui.feedback import FeedbackCollector
from spendsense.features.degradation import GracefulDegradation
from spendsense.features.aggregator import SignalAggregator


def scenario_1_new_user_journey():
    """Scenario 1: New user signs up and goes through onboarding"""
    print("\n" + "="*70)
    print("SCENARIO 1: New User Journey")
    print("="*70)
    
    db_manager = SQLiteManager()
    db_manager.connect()
    
    try:
        # Find a user without consent
        cursor = db_manager.conn.cursor()
        cursor.execute("""
            SELECT user_id FROM users 
            WHERE consent_status = 0 
            LIMIT 1
        """)
        result = cursor.fetchone()
        
        if not result:
            print("\n⚠️  No users without consent found. Creating test user...")
            # Create a test user
            from datetime import datetime
            cursor.execute("""
                INSERT INTO users (user_id, created_at, last_updated, consent_status)
                VALUES (?, ?, ?, ?)
            """, ("test_user_new", datetime.now(), datetime.now(), False))
            db_manager.conn.commit()
            user_id = "test_user_new"
        else:
            user_id = result['user_id']
        
        print(f"\n👤 User: {user_id}")
        print("\n📋 Step 1: User views dashboard WITHOUT consent")
        print("-" * 70)
        
        consent_manager = ConsentManager(db_manager.conn)
        has_consent = consent_manager.check_consent(user_id)
        print(f"Consent Status: {'✅ Active' if has_consent else '❌ Not Provided'}")
        
        if not has_consent:
            print("\n⚠️  User sees consent required message")
            print("   'To view your personalized financial insights, please provide consent.'")
        
        print("\n📋 Step 2: User provides consent")
        print("-" * 70)
        consent_manager.record_consent(user_id)
        print(f"✅ Consent recorded for {user_id}")
        
        print("\n📋 Step 3: System assigns persona")
        print("-" * 70)
        persona_assigner = PersonaAssigner(db_manager.conn)
        assignment = persona_assigner.assign_and_save(user_id)
        print(f"✅ Assigned Persona: {assignment['persona_name']}")
        print(f"   Priority Level: {assignment['priority_level']}")
        print(f"   Signal Strength: {assignment['signal_strength']:.2f}")
        
        print("\n📋 Step 4: System generates recommendations")
        print("-" * 70)
        recommendation_engine = RecommendationEngine(db_manager.conn)
        recommendations = recommendation_engine.generate_and_save(user_id)
        
        education = [r for r in recommendations if r.type == 'education']
        offers = [r for r in recommendations if r.type == 'offer']
        
        print(f"✅ Generated {len(recommendations)} recommendations:")
        print(f"   Education: {len(education)}")
        print(f"   Offers: {len(offers)}")
        
        print("\n📋 Step 5: User views recommendations")
        print("-" * 70)
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"\n{i}. {rec.title}")
            print(f"   Type: {rec.type}")
            print(f"   Rationale: {rec.rationale[:100]}...")
        
        print("\n✅ Scenario 1 Complete: New user successfully onboarded!")
        
        return user_id
    
    finally:
        db_manager.close()


def scenario_2_feedback_collection():
    """Scenario 2: User provides feedback on recommendations"""
    print("\n" + "="*70)
    print("SCENARIO 2: Feedback Collection")
    print("="*70)
    
    db_manager = SQLiteManager()
    db_manager.connect()
    
    try:
        # Find user with recommendations
        cursor = db_manager.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT user_id FROM recommendations 
            LIMIT 1
        """)
        result = cursor.fetchone()
        
        if not result:
            print("\n⚠️  No users with recommendations found.")
            print("   Run Scenario 1 first to generate recommendations.")
            return
        
        user_id = result['user_id']
        print(f"\n👤 User: {user_id}")
        
        recommendation_engine = RecommendationEngine(db_manager.conn)
        feedback_collector = FeedbackCollector(db_manager.conn)
        
        recommendations = recommendation_engine.get_recommendations(user_id)
        
        if not recommendations:
            print("\n⚠️  No recommendations found for user.")
            return
        
        print(f"\n📋 User has {len(recommendations)} recommendations")
        print("\n📋 Step 1: User interacts with recommendations")
        print("-" * 70)
        
        # Simulate different feedback scenarios
        feedback_scenarios = [
            {"thumbs_up": True, "helped_me": True, "applied_this": False, "note": "Very helpful!"},
            {"thumbs_up": True, "helped_me": False, "applied_this": True, "note": "I applied this"},
            {"thumbs_up": False, "helped_me": False, "applied_this": False, "note": "Not relevant"},
        ]
        
        for i, rec in enumerate(recommendations[:3]):
            if i >= len(feedback_scenarios):
                break
            
            scenario = feedback_scenarios[i]
            print(f"\n  Recommendation: {rec['title']}")
            
            feedback_id = feedback_collector.submit_feedback(
                recommendation_id=rec['recommendation_id'],
                user_id=user_id,
                thumbs_up=scenario['thumbs_up'],
                helped_me=scenario['helped_me'],
                applied_this=scenario['applied_this'],
                free_text=scenario['note']
            )
            
            print(f"  ✅ Feedback submitted:")
            print(f"     Thumbs Up: {scenario['thumbs_up']}")
            print(f"     Helped Me: {scenario['helped_me']}")
            print(f"     Applied This: {scenario['applied_this']}")
            print(f"     Note: {scenario['note']}")
        
        print("\n📋 Step 2: Review feedback summary")
        print("-" * 70)
        user_feedback = feedback_collector.get_user_feedback(user_id)
        print(f"✅ Total feedback submissions: {len(user_feedback)}")
        
        thumbs_up_count = sum(1 for f in user_feedback if f.get('thumbs_up'))
        helpful_count = sum(1 for f in user_feedback if f.get('helped_me'))
        applied_count = sum(1 for f in user_feedback if f.get('applied_this'))
        
        print(f"   Thumbs Up: {thumbs_up_count}")
        print(f"   Helped Me: {helpful_count}")
        print(f"   Applied This: {applied_count}")
        
        print("\n✅ Scenario 2 Complete: Feedback successfully collected!")
        
    finally:
        db_manager.close()


def scenario_3_consent_revocation():
    """Scenario 3: User revokes consent"""
    print("\n" + "="*70)
    print("SCENARIO 3: Consent Revocation")
    print("="*70)
    
    db_manager = SQLiteManager()
    db_manager.connect()
    
    try:
        # Find user with consent and recommendations
        cursor = db_manager.conn.cursor()
        cursor.execute("""
            SELECT user_id FROM users 
            WHERE consent_status = 1 
            AND user_id IN (SELECT DISTINCT user_id FROM recommendations)
            LIMIT 1
        """)
        result = cursor.fetchone()
        
        if not result:
            print("\n⚠️  No users with consent and recommendations found.")
            print("   Run Scenario 1 first.")
            return
        
        user_id = result['user_id']
        print(f"\n👤 User: {user_id}")
        
        consent_manager = ConsentManager(db_manager.conn)
        recommendation_engine = RecommendationEngine(db_manager.conn)
        
        print("\n📋 Step 1: Check current state")
        print("-" * 70)
        has_consent = consent_manager.check_consent(user_id)
        recommendations_before = recommendation_engine.get_recommendations(user_id)
        
        print(f"Consent Status: {'✅ Active' if has_consent else '❌ Not Provided'}")
        print(f"Recommendations: {len(recommendations_before)}")
        
        print("\n📋 Step 2: User revokes consent")
        print("-" * 70)
        consent_manager.revoke_consent(user_id)
        print("✅ Consent revoked")
        
        print("\n📋 Step 3: Verify recommendations removed")
        print("-" * 70)
        recommendations_after = recommendation_engine.get_recommendations(user_id)
        has_consent_after = consent_manager.check_consent(user_id)
        
        print(f"Consent Status: {'✅ Active' if has_consent_after else '❌ Not Provided'}")
        print(f"Recommendations: {len(recommendations_after)} (was {len(recommendations_before)})")
        
        if len(recommendations_after) == 0:
            print("✅ All recommendations successfully removed")
        else:
            print("⚠️  Some recommendations still exist")
        
        print("\n✅ Scenario 3 Complete: Consent revocation working correctly!")
        
    finally:
        db_manager.close()


def scenario_4_different_personas():
    """Scenario 4: Explore different persona assignments"""
    print("\n" + "="*70)
    print("SCENARIO 4: Different Persona Assignments")
    print("="*70)
    
    db_manager = SQLiteManager()
    db_manager.connect()
    
    try:
        cursor = db_manager.conn.cursor()
        cursor.execute("""
            SELECT persona_name, COUNT(*) as count
            FROM personas
            GROUP BY persona_name
            ORDER BY count DESC
        """)
        
        persona_distribution = cursor.fetchall()
        
        print("\n📊 Persona Distribution:")
        print("-" * 70)
        for row in persona_distribution:
            print(f"  {row['persona_name']}: {row['count']} users")
        
        print("\n📋 Step 1: View users for each persona")
        print("-" * 70)
        
        persona_assigner = PersonaAssigner(db_manager.conn)
        recommendation_engine = RecommendationEngine(db_manager.conn)
        
        for row in persona_distribution[:3]:  # Show top 3
            persona_name = row['persona_name']
            print(f"\n  👤 {persona_name}:")
            
            # Get a sample user with this persona
            cursor.execute("""
                SELECT user_id FROM personas 
                WHERE persona_name = ? 
                LIMIT 1
            """, (persona_name,))
            
            user_result = cursor.fetchone()
            if user_result:
                user_id = user_result['user_id']
                assignment = persona_assigner.get_assignment(user_id)
                recommendations = recommendation_engine.get_recommendations(user_id)
                
                print(f"     Sample User: {user_id}")
                print(f"     Priority: {assignment['priority_level']}")
                print(f"     Signal Strength: {assignment['signal_strength']:.2f}")
                print(f"     Recommendations: {len(recommendations)}")
                
                # Show sample recommendation
                if recommendations:
                    sample = recommendations[0]
                    print(f"     Sample: {sample['title'][:50]}...")
        
        print("\n✅ Scenario 4 Complete: Different personas explored!")
        
    finally:
        db_manager.close()


def scenario_5_system_health():
    """Scenario 5: Check system health and metrics"""
    print("\n" + "="*70)
    print("SCENARIO 5: System Health & Metrics")
    print("="*70)
    
    db_manager = SQLiteManager()
    db_manager.connect()
    
    try:
        from spendsense.operator.analytics import AnalyticsManager
        from spendsense.operator.health import SystemHealthMonitor
        
        analytics = AnalyticsManager(db_manager.conn)
        health = SystemHealthMonitor(db_manager.conn)
        
        print("\n📊 Coverage Metrics:")
        print("-" * 70)
        coverage = analytics.get_coverage_metrics()
        print(f"  Persona Coverage: {coverage['persona_coverage']}%")
        print(f"  Recommendation Coverage: {coverage['recommendation_coverage']}%")
        print(f"  Explainability: {coverage['explainability_rate']}%")
        print(f"  Auditability: {coverage['auditability_rate']}%")
        
        print("\n💬 Engagement Metrics:")
        print("-" * 70)
        engagement = analytics.get_engagement_metrics()
        print(f"  Total Feedback: {engagement['total_feedback']}")
        print(f"  Helpfulness Score: {engagement['helpfulness_score']}%")
        print(f"  Engagement Rate: {engagement['engagement_rate']}%")
        
        print("\n🏥 System Health:")
        print("-" * 70)
        health_status = health.get_system_health()
        print(f"  Consent Rate: {health_status['consent']['consent_rate']}%")
        print(f"  Estimated Latency: {health_status['latency']['estimated_latency_per_user_seconds']}s")
        print(f"  Data Quality: {health_status['data_quality']['overall_status']}")
        
        print("\n✅ Scenario 5 Complete: System health checked!")
        
    finally:
        db_manager.close()


def run_all_scenarios():
    """Run all user testing scenarios"""
    print("="*70)
    print("SpendSense User Testing - All Scenarios")
    print("="*70)
    
    scenarios = [
        ("1", "New User Journey", scenario_1_new_user_journey),
        ("2", "Feedback Collection", scenario_2_feedback_collection),
        ("3", "Consent Revocation", scenario_3_consent_revocation),
        ("4", "Different Personas", scenario_4_different_personas),
        ("5", "System Health", scenario_5_system_health),
    ]
    
    print("\nAvailable scenarios:")
    for num, name, _ in scenarios:
        print(f"  {num}. {name}")
    
    choice = input("\nRun all scenarios? (y/n) or enter scenario number: ").strip().lower()
    
    if choice == 'y' or choice == 'yes':
        for num, name, func in scenarios:
            try:
                func()
            except Exception as e:
                print(f"\n❌ Error in scenario {num}: {e}")
                import traceback
                traceback.print_exc()
    elif choice in ['1', '2', '3', '4', '5']:
        num, name, func = scenarios[int(choice) - 1]
        print(f"\nRunning Scenario {num}: {name}")
        func()
    else:
        print("\nInvalid choice. Exiting.")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        scenario_num = sys.argv[1]
        scenarios = {
            '1': scenario_1_new_user_journey,
            '2': scenario_2_feedback_collection,
            '3': scenario_3_consent_revocation,
            '4': scenario_4_different_personas,
            '5': scenario_5_system_health,
        }
        
        if scenario_num in scenarios:
            scenarios[scenario_num]()
        else:
            print(f"Invalid scenario number: {scenario_num}")
            print("Available: 1, 2, 3, 4, 5")
    else:
        run_all_scenarios()

