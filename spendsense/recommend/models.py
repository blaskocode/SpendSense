"""Data models for recommendations"""

from dataclasses import dataclass


@dataclass
class Recommendation:
    """Recommendation data structure"""
    recommendation_id: str
    user_id: str
    persona_name: str
    type: str  # 'education' or 'offer'
    title: str
    rationale: str
    generated_at: str
    operator_status: str = 'pending'
    description: str = ''  # Optional description (for AI-generated recommendations)

