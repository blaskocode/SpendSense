"""Unit tests for rationale generation"""

import pytest
from spendsense.recommend.rationale import RationaleGenerator


def test_rationale_generation_format():
    """Test rationale generation format"""
    generator = RationaleGenerator()
    
    # Test rationale generation
    test_cases = [
        {
            'persona_name': 'Credit Builder',
            'signals': {'credit': {'credit_utilization': 0.0}},
            'recommendation_type': 'education'
        },
        {
            'persona_name': 'High Utilization',
            'signals': {'credit': {'credit_utilization': 75.0}},
            'recommendation_type': 'offer'
        }
    ]
    
    for case in test_cases:
        rationale = generator.generate_rationale(
            persona_name=case['persona_name'],
            signals=case['signals'],
            recommendation_type=case['recommendation_type']
        )
        
        # Should return a string rationale
        assert isinstance(rationale, str)
        assert len(rationale) > 0
        # Should contain "because" or explanatory language
        assert 'because' in rationale.lower() or 'your' in rationale.lower()

