#!/usr/bin/env python3
"""User-facing view for testing recommendations"""

import sqlite3
import json
from spendsense.storage.sqlite_manager import SQLiteManager
from spendsense.guardrails.consent import ConsentManager
from spendsense.personas.assignment import PersonaAssigner
from spendsense.recommend.engine import RecommendationEngine
from spendsense.ui.feedback import FeedbackCollector
from spendsense.features.aggregator import SignalAggregator
from spendsense.features.degradation import GracefulDegradation

def display_user_dashboard(user_id: str):
    """Display user dashboard view"""
    db_manager = SQLiteManager()
    db_manager.connect()
    
    try:
        consent_manager = ConsentManager(db_manager.conn)
        persona_assigner = PersonaAssigner(db_manager.conn)
        recommendation_engine = RecommendationEngine(db_manager.conn)
        feedback_collector = FeedbackCollector(db_manager.conn)
        aggregator = SignalAggregator(db_manager.conn)
        degradation = GracefulDegradation(aggregator)
        
        # Check consent
        has_consent = consent_manager.check_consent(user_id)
        
        print("\n" + "="*70)
        print(f"SpendSense Dashboard - User: {user_id}")
        print("="*70)
        
        if not has_consent:
            print("\n⚠️  CONSENT REQUIRED")
            print("\nTo view your personalized financial insights, please provide consent.")
            print("This allows us to analyze your transaction data and generate recommendations.")
            print("\nWould you like to provide consent? (This is a demo - consent is simulated)")
            return
        
        # Get persona
        assignment = persona_assigner.get_assignment(user_id)
        if not assignment:
            assignment = persona_assigner.assign_and_save(user_id)
        
        persona_name = assignment['persona_name']
        
        # Header
        print(f"\n👋 Welcome! You're a {persona_name}")
        print(f"   Priority Level: {assignment['priority_level']}")
        print(f"   Signal Strength: {assignment['signal_strength']:.2f}")
        
        # Get signals
        signals = degradation.get_primary_signals(user_id)
        data_availability = degradation.get_signals_with_degradation(user_id).get('data_availability', 'unknown')
        
        if data_availability == 'new':
            print("\n📊 Insights: We're still learning about your financial patterns.")
            print("   As we gather more data, your insights will become more personalized.")
        else:
            # Top 3 Behavioral Signals
            print("\n📊 Your Top Behavioral Signals:")
            
            credit_signals = signals.get('credit', {})
            subscriptions = signals.get('subscriptions', {})
            savings = signals.get('savings', {})
            income = signals.get('income', {})
            
            signals_list = []
            
            if credit_signals.get('credit_utilization', 0) > 0:
                signals_list.append({
                    'name': 'Credit Utilization',
                    'value': f"{credit_signals['credit_utilization']:.1f}%",
                    'description': f"Your credit utilization is {credit_signals['credit_utilization']:.1f}%"
                })
            
            if subscriptions.get('subscriptions_count', 0) > 0:
                signals_list.append({
                    'name': 'Subscriptions',
                    'value': f"{subscriptions['subscriptions_count']} active",
                    'description': f"You have {subscriptions['subscriptions_count']} recurring subscriptions"
                })
            
            if savings.get('savings_growth_rate', 0) != 0:
                signals_list.append({
                    'name': 'Savings Growth',
                    'value': f"{savings['savings_growth_rate']:.1f}%",
                    'description': f"Your savings are growing at {savings['savings_growth_rate']:.1f}%"
                })
            
            for i, signal in enumerate(signals_list[:3], 1):
                print(f"   {i}. {signal['name']}: {signal['value']}")
                print(f"      {signal['description']}")
        
        # Get recommendations
        recommendations = recommendation_engine.get_recommendations(user_id)
        
        if not recommendations:
            # Generate if none exist
            recommendations = recommendation_engine.generate_and_save(user_id)
            recommendations = recommendation_engine.get_recommendations(user_id)
        
        education = [r for r in recommendations if r['type'] == 'education']
        offers = [r for r in recommendations if r['type'] == 'offer']
        
        # Your Plan (Education)
        print("\n" + "="*70)
        print("📚 Your Plan")
        print("="*70)
        
        for i, rec in enumerate(education[:5], 1):
            print(f"\n{i}. {rec['title']}")
            print(f"   {rec['rationale'][:150]}...")
            print(f"   Status: {rec['operator_status']}")
        
        # Partner Offers
        if offers:
            print("\n" + "="*70)
            print("💼 Partner Offers")
            print("="*70)
            
            for i, rec in enumerate(offers[:3], 1):
                print(f"\n{i}. {rec['title']}")
                print(f"   {rec['rationale'][:150]}...")
                print(f"   Status: {rec['operator_status']}")
        
        # Data freshness
        print("\n" + "="*70)
        print("ℹ️  Data Information")
        print("="*70)
        print(f"Data Availability: {data_availability}")
        if recommendations:
            latest = max(r['generated_at'] for r in recommendations)
            print(f"Last Updated: {latest}")
        print("\n⚠️  This is educational content, not financial advice.")
        print("    Consult a licensed financial advisor for personalized guidance.")
        
        # Feedback prompt
        print("\n" + "="*70)
        print("💬 Feedback")
        print("="*70)
        print("You can provide feedback on recommendations using the feedback system.")
        print(f"Total feedback submissions: {len(feedback_collector.get_user_feedback(user_id))}")
        
        print("\n" + "="*70)
        
    finally:
        db_manager.close()

def list_users():
    """List available users for testing"""
    db_manager = SQLiteManager()
    db_manager.connect()
    
    try:
        cursor = db_manager.conn.cursor()
        cursor.execute("""
            SELECT user_id, consent_status
            FROM users
            ORDER BY user_id
            LIMIT 20
        """)
        
        users = cursor.fetchall()
        
        print("\nAvailable Users:")
        print("-" * 70)
        for user in users:
            consent_status = "✅" if user['consent_status'] else "❌"
            print(f"{consent_status} {user['user_id']}")
        
        return [user['user_id'] for user in users]
    
    finally:
        db_manager.close()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
        display_user_dashboard(user_id)
    else:
        print("SpendSense User View")
        print("\nUsage: python user_view.py <user_id>")
        print("\nAvailable users:")
        users = list_users()
        if users:
            print(f"\nExample: python user_view.py {users[0]}")

