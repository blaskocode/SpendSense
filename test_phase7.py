#!/usr/bin/env python3
"""Test Phase 7: Evaluation & Metrics"""

import sqlite3
from spendsense.storage.sqlite_manager import SQLiteManager
from spendsense.guardrails.consent import ConsentManager
from spendsense.personas.assignment import PersonaAssigner
from spendsense.recommend.engine import RecommendationEngine
from spendsense.eval.scoring import ScoringSystem
from spendsense.eval.satisfaction import SatisfactionMetrics
from spendsense.eval.fairness import FairnessAnalyzer
from spendsense.eval.reporter import EvaluationReporter

def test_phase7():
    """Test Phase 7 evaluation components"""
    print("="*70)
    print("Phase 7: Evaluation & Metrics Test")
    print("="*70)
    print()
    
    # Connect to database
    db_manager = SQLiteManager()
    db_manager.connect()
    
    try:
        # Setup: Ensure we have some users with personas and recommendations
        consent_manager = ConsentManager(db_manager.conn)
        persona_assigner = PersonaAssigner(db_manager.conn)
        recommendation_engine = RecommendationEngine(db_manager.conn)
        
        cursor = db_manager.conn.cursor()
        cursor.execute("SELECT user_id FROM users LIMIT 10")
        test_users = [row['user_id'] for row in cursor.fetchall()]
        
        print("Setting up test data...")
        for user_id in test_users:
            consent_manager.record_consent(user_id)
            persona_assigner.assign_and_save(user_id)
            recommendation_engine.generate_and_save(user_id)
        print(f"✅ Setup complete for {len(test_users)} users\n")
        
        # Test 1: Automatic Scoring
        print("="*70)
        print("Test 1: Automatic Scoring System")
        print("="*70)
        
        scoring = ScoringSystem(db_manager.conn)
        
        coverage = scoring.compute_coverage_score()
        print(f"\nCoverage Score:")
        print(f"  Rate: {coverage['coverage_rate']}% (Target: {coverage['target']}%)")
        print(f"  Users with Persona + 3+ Behaviors: {coverage['users_with_persona_and_behaviors']}")
        print(f"  Status: {'✅' if coverage['meets_target'] else '❌'}")
        
        explainability = scoring.compute_explainability_score()
        print(f"\nExplainability Score:")
        print(f"  Rate: {explainability['explainability_rate']}% (Target: {explainability['target']}%)")
        print(f"  Recommendations with Rationales: {explainability['recommendations_with_rationales']}")
        print(f"  Status: {'✅' if explainability['meets_target'] else '❌'}")
        
        latency = scoring.compute_latency_score(sample_size=5)
        print(f"\nLatency Score:")
        print(f"  Avg: {latency['avg_latency_seconds']}s (Target: <{latency['target']}s)")
        print(f"  Min: {latency['min_latency_seconds']}s, Max: {latency['max_latency_seconds']}s")
        print(f"  Status: {'✅' if latency['meets_target'] else '❌'}")
        
        auditability = scoring.compute_auditability_score()
        print(f"\nAuditability Score:")
        print(f"  Rate: {auditability['auditability_rate']}% (Target: {auditability['target']}%)")
        print(f"  Users with Traces: {auditability['users_with_traces']}")
        print(f"  Status: {'✅' if auditability['meets_target'] else '❌'}")
        
        # Test 2: User Satisfaction Metrics
        print("\n" + "="*70)
        print("Test 2: User Satisfaction Metrics")
        print("="*70)
        
        satisfaction = SatisfactionMetrics(db_manager.conn)
        
        engagement = satisfaction.compute_engagement_rate()
        print(f"\nEngagement Rate:")
        print(f"  Rate: {engagement['engagement_rate']}%")
        print(f"  Recommendations with Feedback: {engagement['recommendations_with_feedback']}")
        print(f"  User Engagement: {engagement['user_engagement_rate']}%")
        
        helpfulness = satisfaction.compute_helpfulness_score()
        print(f"\nHelpfulness Score:")
        print(f"  Score: {helpfulness['helpfulness_score']}%")
        print(f"  Thumbs Up: {helpfulness['thumbs_up']}, Down: {helpfulness['thumbs_down']}")
        
        action = satisfaction.compute_action_rate()
        print(f"\nAction Rate:")
        print(f"  Applied This: {action['action_rate']}%")
        print(f"  Helped Me: {action['helped_rate']}%")
        
        # Test 3: Fairness Analysis
        print("\n" + "="*70)
        print("Test 3: Fairness Analysis")
        print("="*70)
        
        fairness = FairnessAnalyzer(db_manager.conn)
        
        quartiles = fairness.detect_income_quartiles()
        print(f"\nIncome Quartiles:")
        for q, users in quartiles.items():
            print(f"  {q.upper()}: {len(users)} users")
        
        persona_dist = fairness.analyze_persona_distribution_by_income()
        print(f"\nPersona Distribution by Income:")
        for q, data in persona_dist.items():
            print(f"  {q.upper()}: {data.get('total_users', 0)} users")
            for persona, count in data.get('persona_distribution', {}).items():
                print(f"    - {persona}: {count}")
        
        rec_counts = fairness.analyze_recommendation_count_by_income()
        print(f"\nRecommendation Counts by Income:")
        for q, data in rec_counts.items():
            print(f"  {q.upper()}: Avg {data.get('avg_recommendations', 0)} recommendations")
        
        bias = fairness.detect_systematic_bias()
        print(f"\nBias Detection:")
        print(f"  Q1/Q4 Ratio: {bias['recommendation_ratio_q1_to_q4']}")
        print(f"  Bias Detected: {'⚠️ Yes' if bias['overall_bias_detected'] else '✅ No'}")
        
        # Test 4: Report Generation
        print("\n" + "="*70)
        print("Test 4: Report Generation")
        print("="*70)
        
        reporter = EvaluationReporter(db_manager.conn)
        
        print("\nGenerating full evaluation report...")
        results = reporter.run_full_evaluation(latency_sample_size=5)
        
        print("\n✅ Generated output files:")
        for file_type, file_path in results['output_files'].items():
            print(f"  {file_type}: {file_path}")
        
        print("\n" + "="*70)
        print("Phase 7 Test Complete!")
        print("="*70)
        
    finally:
        db_manager.close()

if __name__ == '__main__':
    test_phase7()

