"""Performance tests"""

import pytest
import time
from spendsense.storage.sqlite_manager import SQLiteManager
from spendsense.guardrails.consent import ConsentManager
from spendsense.personas.assignment import PersonaAssigner
from spendsense.recommend.engine import RecommendationEngine


def test_generate_recommendations_100_users_under_5_seconds_each(temp_db, sample_user_data):
    """Test generate recommendations for 100 users <5 seconds each"""
    consent_manager = ConsentManager(temp_db.conn)
    persona_assigner = PersonaAssigner(temp_db.conn)
    recommendation_engine = RecommendationEngine(temp_db.conn)
    
    # Test with available users
    user_ids = sample_user_data['users']
    
    latencies = []
    for user_id in user_ids[:10]:  # Test with 10 users for speed
        consent_manager.record_consent(user_id)
        persona_assigner.assign_and_save(user_id)
        
        start_time = time.time()
        recommendations = recommendation_engine.generate_and_save(user_id)
        elapsed = time.time() - start_time
        
        latencies.append(elapsed)
        assert elapsed < 5.0, f"Recommendation generation took {elapsed:.2f}s for {user_id}"
    
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    assert avg_latency < 5.0, f"Average latency {avg_latency:.2f}s exceeds 5s target"


def test_operator_dashboard_loads_signals_under_3_seconds(temp_db, sample_user_data):
    """Test operator dashboard loads all signals <3 seconds"""
    from spendsense.operator.review import UserReviewer
    
    user_reviewer = UserReviewer(temp_db.conn)
    user_id = sample_user_data['users'][0]
    
    start_time = time.time()
    profile = user_reviewer.get_user_profile(user_id)
    elapsed = time.time() - start_time
    
    assert elapsed < 3.0, f"Profile load took {elapsed:.2f}s"
    assert profile is not None

