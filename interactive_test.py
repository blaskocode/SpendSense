#!/usr/bin/env python3
"""Interactive testing interface for SpendSense"""

import sqlite3
from spendsense.storage.sqlite_manager import SQLiteManager
from spendsense.guardrails.consent import ConsentManager
from spendsense.personas.assignment import PersonaAssigner
from spendsense.recommend.engine import RecommendationEngine
from spendsense.ui.feedback import FeedbackCollector
from spendsense.operator.review import UserReviewer
from spendsense.operator.analytics import AnalyticsManager

def show_menu():
    """Display main menu"""
    print("\n" + "="*70)
    print("SpendSense Interactive Testing")
    print("="*70)
    print("\n1. View User Dashboard")
    print("2. Test Consent Flow")
    print("3. View Persona Assignment")
    print("4. Generate Recommendations")
    print("5. Submit Feedback")
    print("6. View Operator Analytics")
    print("7. View User Profile (Operator View)")
    print("8. Run End-to-End Test")
    print("9. Exit")
    print("\n" + "="*70)

def get_user_id():
    """Get user ID from user"""
    db_manager = SQLiteManager()
    db_manager.connect()
    
    try:
        cursor = db_manager.conn.cursor()
        cursor.execute("SELECT user_id FROM users LIMIT 10")
        users = [row['user_id'] for row in cursor.fetchall()]
        
        print("\nAvailable users:")
        for i, user_id in enumerate(users, 1):
            print(f"  {i}. {user_id}")
        
        choice = input("\nEnter user number or user_id: ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(users):
            return users[int(choice) - 1]
        elif choice in users:
            return choice
        else:
            print(f"Invalid choice. Using {users[0]}")
            return users[0]
    finally:
        db_manager.close()

def main():
    """Main interactive loop"""
    db_manager = SQLiteManager()
    db_manager.connect()
    
    try:
        consent_manager = ConsentManager(db_manager.conn)
        persona_assigner = PersonaAssigner(db_manager.conn)
        recommendation_engine = RecommendationEngine(db_manager.conn)
        feedback_collector = FeedbackCollector(db_manager.conn)
        user_reviewer = UserReviewer(db_manager.conn)
        analytics = AnalyticsManager(db_manager.conn)
        
        while True:
            show_menu()
            choice = input("\nEnter choice (1-9): ").strip()
            
            if choice == '1':
                # View User Dashboard
                user_id = get_user_id()
                print(f"\n{'='*70}")
                print(f"User Dashboard: {user_id}")
                print(f"{'='*70}")
                
                has_consent = consent_manager.check_consent(user_id)
                print(f"\nConsent Status: {'✅ Active' if has_consent else '❌ Not Provided'}")
                
                if not has_consent:
                    print("\n⚠️  User needs to provide consent first.")
                    continue
                
                # Get persona
                assignment = persona_assigner.get_assignment(user_id)
                if assignment:
                    print(f"\nPersona: {assignment['persona_name']}")
                    print(f"Priority Level: {assignment['priority_level']}")
                    print(f"Signal Strength: {assignment['signal_strength']:.2f}")
                
                # Get recommendations
                recommendations = recommendation_engine.get_recommendations(user_id)
                if not recommendations:
                    print("\nGenerating recommendations...")
                    recommendations = recommendation_engine.generate_and_save(user_id)
                    recommendations = recommendation_engine.get_recommendations(user_id)
                
                education = [r for r in recommendations if r['type'] == 'education']
                offers = [r for r in recommendations if r['type'] == 'offer']
                
                print(f"\n📚 Education Recommendations: {len(education)}")
                for i, rec in enumerate(education[:3], 1):
                    print(f"   {i}. {rec['title']}")
                
                print(f"\n💼 Partner Offers: {len(offers)}")
                for i, rec in enumerate(offers[:3], 1):
                    print(f"   {i}. {rec['title']}")
            
            elif choice == '2':
                # Test Consent Flow
                user_id = get_user_id()
                print(f"\n{'='*70}")
                print(f"Consent Flow Test: {user_id}")
                print(f"{'='*70}")
                
                current_status = consent_manager.check_consent(user_id)
                print(f"\nCurrent Status: {'✅ Has Consent' if current_status else '❌ No Consent'}")
                
                action = input("\n[r] Record consent, [v] Revoke consent, [c] Cancel: ").strip().lower()
                
                if action == 'r':
                    consent_manager.record_consent(user_id)
                    print("✅ Consent recorded!")
                elif action == 'v':
                    consent_manager.revoke_consent(user_id)
                    print("✅ Consent revoked! Recommendations deleted.")
            
            elif choice == '3':
                # View Persona Assignment
                user_id = get_user_id()
                print(f"\n{'='*70}")
                print(f"Persona Assignment: {user_id}")
                print(f"{'='*70}")
                
                assignment = persona_assigner.assign_and_save(user_id)
                
                print(f"\nAssigned Persona: {assignment['persona_name']}")
                print(f"Priority Level: {assignment['priority_level']}")
                print(f"Signal Strength: {assignment['signal_strength']:.2f}")
                
                import json
                trace = json.loads(assignment['decision_trace']) if isinstance(assignment['decision_trace'], str) else assignment['decision_trace']
                print(f"\nDecision Reason: {trace.get('reason', 'unknown')}")
                if 'all_matched_personas' in trace:
                    print(f"All Matched Personas: {', '.join(trace['all_matched_personas'])}")
            
            elif choice == '4':
                # Generate Recommendations
                user_id = get_user_id()
                print(f"\n{'='*70}")
                print(f"Generate Recommendations: {user_id}")
                print(f"{'='*70}")
                
                if not consent_manager.check_consent(user_id):
                    print("\n⚠️  User must provide consent first!")
                    continue
                
                print("\nGenerating recommendations...")
                recommendations = recommendation_engine.generate_and_save(user_id)
                
                education = [r for r in recommendations if r.type == 'education']
                offers = [r for r in recommendations if r.type == 'offer']
                
                print(f"\n✅ Generated {len(recommendations)} recommendations:")
                print(f"   Education: {len(education)}")
                print(f"   Offers: {len(offers)}")
                
                print("\nSample recommendations:")
                for rec in recommendations[:3]:
                    print(f"\n   • {rec.title}")
                    print(f"     {rec.rationale[:100]}...")
            
            elif choice == '5':
                # Submit Feedback
                user_id = get_user_id()
                print(f"\n{'='*70}")
                print(f"Submit Feedback: {user_id}")
                print(f"{'='*70}")
                
                recommendations = recommendation_engine.get_recommendations(user_id)
                if not recommendations:
                    print("\nNo recommendations found. Generate recommendations first.")
                    continue
                
                print("\nAvailable recommendations:")
                for i, rec in enumerate(recommendations[:5], 1):
                    print(f"   {i}. {rec['title']} ({rec['type']})")
                
                try:
                    rec_num = int(input("\nSelect recommendation (1-5): ")) - 1
                    if 0 <= rec_num < len(recommendations):
                        rec = recommendations[rec_num]
                        
                        thumbs = input("Thumbs up? [y/n]: ").strip().lower()
                        thumbs_up = thumbs == 'y' if thumbs else None
                        
                        helped = input("Helped you? [y/n/skip]: ").strip().lower()
                        helped_me = helped == 'y' if helped else None
                        
                        applied = input("Applied this? [y/n/skip]: ").strip().lower()
                        applied_this = applied == 'y' if applied else None
                        
                        feedback_id = feedback_collector.submit_feedback(
                            recommendation_id=rec['recommendation_id'],
                            user_id=user_id,
                            thumbs_up=thumbs_up,
                            helped_me=helped_me,
                            applied_this=applied_this
                        )
                        print(f"\n✅ Feedback submitted! ID: {feedback_id}")
                    else:
                        print("Invalid selection")
                except ValueError:
                    print("Invalid input")
            
            elif choice == '6':
                # View Operator Analytics
                print(f"\n{'='*70}")
                print("Operator Analytics")
                print(f"{'='*70}")
                
                # Coverage
                coverage = analytics.get_coverage_metrics()
                print(f"\n📊 Coverage Metrics:")
                print(f"   Persona Coverage: {coverage['persona_coverage']}%")
                print(f"   Recommendation Coverage: {coverage['recommendation_coverage']}%")
                print(f"   Explainability: {coverage['explainability_rate']}%")
                print(f"   Auditability: {coverage['auditability_rate']}%")
                
                # Engagement
                engagement = analytics.get_engagement_metrics()
                print(f"\n💬 Engagement Metrics:")
                print(f"   Total Feedback: {engagement['total_feedback']}")
                print(f"   Helpfulness Score: {engagement['helpfulness_score']}%")
                print(f"   Engagement Rate: {engagement['engagement_rate']}%")
                
                # Persona Distribution
                persona_dist = analytics.get_persona_distribution()
                print(f"\n👥 Persona Distribution:")
                for persona, count in sorted(persona_dist.items(), key=lambda x: -x[1]):
                    print(f"   {persona}: {count} users")
            
            elif choice == '7':
                # View User Profile (Operator View)
                user_id = get_user_id()
                print(f"\n{'='*70}")
                print(f"Operator View: {user_id}")
                print(f"{'='*70}")
                
                profile = user_reviewer.get_user_profile(user_id)
                
                print(f"\nUser: {profile['user_id']}")
                print(f"Consent: {'✅ Active' if profile['consent_status'] else '❌ Not Provided'}")
                print(f"Data Availability: {profile['data_availability']}")
                print(f"\nPersona: {profile['persona']['persona_name']}")
                print(f"All Matched: {', '.join(profile['persona']['all_matched_personas'])}")
                print(f"\nRecommendations: {profile['recommendation_count']}")
                
                if profile['signals_30d']:
                    credit = profile['signals_30d'].get('credit', {})
                    subs = profile['signals_30d'].get('subscriptions', {})
                    print(f"\n30-Day Signals:")
                    print(f"   Credit Utilization: {credit.get('credit_utilization', 0):.1f}%")
                    print(f"   Subscriptions: {subs.get('subscriptions_count', 0)}")
            
            elif choice == '8':
                # Run End-to-End Test
                print("\nRunning end-to-end test...")
                import subprocess
                subprocess.run(['python3', 'test_end_to_end.py'])
            
            elif choice == '9':
                print("\nExiting...")
                break
            
            else:
                print("\nInvalid choice. Please try again.")
            
            input("\nPress Enter to continue...")
    
    finally:
        db_manager.close()

if __name__ == '__main__':
    main()

