#!/usr/bin/env python3
"""Test script for Phase 6: Operator Dashboard"""

import sqlite3
from spendsense.storage.sqlite_manager import SQLiteManager
from spendsense.operator.review import UserReviewer
from spendsense.operator.approval import ApprovalManager
from spendsense.operator.analytics import AnalyticsManager
from spendsense.operator.feedback_review import FeedbackReviewer
from spendsense.operator.health import SystemHealthMonitor

def test_phase6():
    """Test Phase 6 operator dashboard"""
    print("Testing Phase 6: Operator Dashboard\n")
    
    # Connect to database
    db_manager = SQLiteManager()
    db_manager.connect()
    
    try:
        # Test user review
        print("="*70)
        print("1. Testing User Review")
        print("="*70)
        
        reviewer = UserReviewer(db_manager.conn)
        
        # Search users
        users = reviewer.search_users(limit=5)
        print(f"Found {len(users)} users")
        for user in users[:3]:
            print(f"  {user['user_id']}: {user['persona_name']} (Priority {user['priority_level']})")
        
        # Get user profile
        if users:
            test_user = users[0]['user_id']
            profile = reviewer.get_user_profile(test_user)
            print(f"\nUser Profile for {test_user}:")
            print(f"  Persona: {profile['persona']['persona_name']}")
            print(f"  Data Availability: {profile['data_availability']}")
            print(f"  Recommendations: {profile['recommendation_count']}")
            print(f"  All Matched Personas: {', '.join(profile['persona']['all_matched_personas'])}")
        
        # Test approval queue
        print("\n" + "="*70)
        print("2. Testing Approval Queue")
        print("="*70)
        
        approval_manager = ApprovalManager(db_manager.conn)
        
        # Get approval queue
        queue = approval_manager.get_approval_queue(limit=10)
        print(f"Found {len(queue)} pending recommendations")
        
        if queue:
            # Approve first recommendation
            rec_id = queue[0]['recommendation_id']
            approved = approval_manager.approve_recommendation(rec_id)
            print(f"Approved recommendation {rec_id}: {approved}")
            
            # Test bulk approve
            remaining = approval_manager.get_approval_queue(limit=5)
            if remaining:
                persona = remaining[0]['persona_name']
                count = approval_manager.bulk_approve_by_persona(persona)
                print(f"Bulk approved {count} recommendations for persona {persona}")
        
        # Test analytics
        print("\n" + "="*70)
        print("3. Testing Analytics")
        print("="*70)
        
        analytics = AnalyticsManager(db_manager.conn)
        
        # Persona distribution
        persona_dist = analytics.get_persona_distribution()
        print(f"Persona Distribution:")
        for persona, count in sorted(persona_dist.items(), key=lambda x: -x[1]):
            print(f"  {persona}: {count} users")
        
        # Coverage metrics
        coverage = analytics.get_coverage_metrics()
        print(f"\nCoverage Metrics:")
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
        
        # Test feedback review
        print("\n" + "="*70)
        print("4. Testing Feedback Review")
        print("="*70)
        
        feedback_reviewer = FeedbackReviewer(db_manager.conn)
        
        # Get feedback aggregates
        aggregates = feedback_reviewer.get_feedback_aggregates()
        if aggregates:
            print(f"Feedback Aggregates:")
            for agg in aggregates[:3]:
                print(f"  {agg['type']} ({agg['persona_name']}): "
                      f"{agg['helpfulness_score']}% helpfulness, {agg['action_rate']}% action rate")
        
        # Test system health
        print("\n" + "="*70)
        print("5. Testing System Health")
        print("="*70)
        
        health_monitor = SystemHealthMonitor(db_manager.conn)
        
        health = health_monitor.get_system_health()
        
        print(f"Consent Status:")
        consent = health['consent']
        print(f"  Total Users: {consent['total_users']}")
        print(f"  With Consent: {consent['users_with_consent']} ({consent['consent_rate']}%)")
        
        print(f"\nLatency Metrics:")
        latency = health['latency']
        print(f"  Estimated Latency: {latency['estimated_latency_per_user_seconds']}s per user")
        print(f"  Meets Target (<5s): {latency['meets_target']}")
        
        print(f"\nData Quality Alerts:")
        alerts = health['data_quality_alerts']
        if alerts:
            for alert in alerts:
                print(f"  {alert['severity'].upper()}: {alert['message']}")
        else:
            print("  No alerts")
        
        print("\n" + "="*70)
        print("Phase 6 Test Complete!")
        print("="*70 + "\n")
        
    finally:
        db_manager.close()

if __name__ == '__main__':
    test_phase6()

