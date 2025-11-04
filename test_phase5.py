#!/usr/bin/env python3
"""Test script for Phase 5: Guardrails & User UX"""

import sqlite3
from spendsense.storage.sqlite_manager import SQLiteManager
from spendsense.recommend.engine import RecommendationEngine
from spendsense.guardrails.consent import ConsentManager
from spendsense.guardrails.tone import ToneValidator
from spendsense.ui.feedback import FeedbackCollector

def test_phase5():
    """Test Phase 5 guardrails and feedback"""
    print("Testing Phase 5: Guardrails & User UX\n")
    
    # Connect to database
    db_manager = SQLiteManager()
    db_manager.connect()
    
    try:
        # Test consent management
        print("="*70)
        print("1. Testing Consent Management")
        print("="*70)
        
        consent_manager = ConsentManager(db_manager.conn)
        
        # Test with a sample user
        test_user = "user_001"
        
        # Check initial consent status
        has_consent = consent_manager.check_consent(test_user)
        print(f"User {test_user} initial consent: {has_consent}")
        
        # Record consent
        consent_manager.record_consent(test_user)
        has_consent = consent_manager.check_consent(test_user)
        print(f"After recording consent: {has_consent}")
        
        # Test recommendation generation with consent
        print("\n" + "="*70)
        print("2. Testing Recommendations with Consent")
        print("="*70)
        
        engine = RecommendationEngine(db_manager.conn)
        recommendations = engine.generate_and_save(test_user)
        
        print(f"Generated {len(recommendations)} recommendations")
        education = [r for r in recommendations if r.type == 'education']
        offers = [r for r in recommendations if r.type == 'offer']
        print(f"  Education: {len(education)}")
        print(f"  Offers: {len(offers)}")
        
        # Show sample recommendation with disclosure
        if recommendations:
            sample = recommendations[0]
            print(f"\nSample Recommendation:")
            print(f"  Title: {sample.title}")
            print(f"  Rationale: {sample.rationale[:150]}...")
            print(f"  Has Disclosure: {'not financial advice' in sample.rationale.lower()}")
        
        # Test tone validation
        print("\n" + "="*70)
        print("3. Testing Tone Validation")
        print("="*70)
        
        tone_validator = ToneValidator()
        
        good_text = "Your savings are growing at 5% which is excellent. Consider automating your savings."
        bad_text = "You're overspending and making bad choices with your money."
        
        is_valid, issues = tone_validator.validate_tone(good_text)
        print(f"Good text validation: {is_valid} (issues: {issues})")
        
        is_valid, issues = tone_validator.validate_tone(bad_text)
        print(f"Bad text validation: {is_valid} (issues: {issues})")
        
        sanitized = tone_validator.sanitize_text(bad_text)
        print(f"Sanitized text: {sanitized}")
        
        # Test feedback system
        print("\n" + "="*70)
        print("4. Testing Feedback System")
        print("="*70)
        
        feedback_collector = FeedbackCollector(db_manager.conn)
        
        if recommendations:
            rec_id = recommendations[0].recommendation_id
            
            # Submit feedback
            feedback_id = feedback_collector.submit_feedback(
                recommendation_id=rec_id,
                user_id=test_user,
                thumbs_up=True,
                helped_me=True,
                free_text="This was very helpful!"
            )
            print(f"Submitted feedback: {feedback_id}")
            
            # Get feedback
            feedback = feedback_collector.get_feedback(rec_id)
            print(f"Retrieved {len(feedback)} feedback entries")
        
        # Test consent revocation
        print("\n" + "="*70)
        print("5. Testing Consent Revocation")
        print("="*70)
        
        consent_manager.revoke_consent(test_user)
        has_consent = consent_manager.check_consent(test_user)
        print(f"After revocation: {has_consent}")
        
        # Try to generate recommendations without consent
        recommendations_no_consent = engine.generate_recommendations(test_user)
        print(f"Recommendations without consent: {len(recommendations_no_consent)}")
        
        print("\n" + "="*70)
        print("Phase 5 Test Complete!")
        print("="*70 + "\n")
        
    finally:
        db_manager.close()

if __name__ == '__main__':
    test_phase5()

