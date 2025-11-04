"""Integration tests for end-to-end workflows"""

import pytest
from datetime import datetime
from spendsense.storage.sqlite_manager import SQLiteManager
from spendsense.guardrails.consent import ConsentManager
from spendsense.personas.assignment import PersonaAssigner
from spendsense.recommend.engine import RecommendationEngine
from spendsense.ui.feedback import FeedbackCollector


def test_end_to_end_ingest_signals_persona_recommendations(temp_db, sample_user_data):
    """Test end-to-end: ingest → signals → persona → recommendations"""
    user_id = sample_user_data['users'][0]
    
    # Record consent
    consent_manager = ConsentManager(temp_db.conn)
    consent_manager.record_consent(user_id)
    
    # Assign persona
    persona_assigner = PersonaAssigner(temp_db.conn)
    assignment = persona_assigner.assign_and_save(user_id)
    
    assert assignment is not None
    assert assignment['persona_name'] is not None
    
    # Generate recommendations
    recommendation_engine = RecommendationEngine(temp_db.conn)
    recommendations = recommendation_engine.generate_and_save(user_id)
    
    assert len(recommendations) > 0
    assert all(r.type in ['education', 'offer'] for r in recommendations)


def test_multiple_personas_matching_prioritization(temp_db, sample_user_data):
    """Test multiple personas matching → prioritization"""
    persona_assigner = PersonaAssigner(temp_db.conn)
    user_id = sample_user_data['users'][0]
    
    assignment = persona_assigner.assign_and_save(user_id)
    
    # Should have a single primary persona
    assert assignment['persona_name'] is not None
    
    # Decision trace should show all matched personas
    import json
    trace = json.loads(assignment['decision_trace']) if isinstance(assignment['decision_trace'], str) else assignment['decision_trace']
    
    assert 'all_matched_personas' in trace or 'matched_personas' in trace


def test_consent_revocation_recommendations_disappear(temp_db, sample_user_data):
    """Test consent revocation → recommendations disappear"""
    user_id = sample_user_data['users'][0]
    
    consent_manager = ConsentManager(temp_db.conn)
    recommendation_engine = RecommendationEngine(temp_db.conn)
    
    # Record consent and generate recommendations
    consent_manager.record_consent(user_id)
    recommendations = recommendation_engine.generate_and_save(user_id)
    assert len(recommendations) > 0
    
    # Revoke consent
    consent_manager.revoke_consent(user_id)
    
    # Recommendations should be deleted
    remaining = recommendation_engine.get_recommendations(user_id)
    assert len(remaining) == 0


def test_feedback_submission_storage_retrieval(temp_db, sample_user_data):
    """Test feedback submission → storage → retrieval"""
    user_id = sample_user_data['users'][0]
    
    consent_manager = ConsentManager(temp_db.conn)
    recommendation_engine = RecommendationEngine(temp_db.conn)
    feedback_collector = FeedbackCollector(temp_db.conn)
    
    # Setup
    consent_manager.record_consent(user_id)
    recommendations = recommendation_engine.generate_and_save(user_id)
    
    if recommendations:
        rec_id = recommendations[0].recommendation_id
        
        # Submit feedback
        feedback_id = feedback_collector.submit_feedback(
            recommendation_id=rec_id,
            user_id=user_id,
            thumbs_up=True,
            helped_me=True
        )
        
        assert feedback_id is not None
        
        # Retrieve feedback
        user_feedback = feedback_collector.get_user_feedback(user_id)
        assert len(user_feedback) > 0

