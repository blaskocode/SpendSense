"""Pydantic models for API requests and responses"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# User Management Models
class CreateUserRequest(BaseModel):
    """Request to create a new user"""
    user_id: Optional[str] = None
    generate_synthetic_data: bool = Field(default=True, description="Generate synthetic data for user")


class CreateUserResponse(BaseModel):
    """Response after creating a user"""
    user_id: str
    created_at: datetime
    message: str


class ConsentRequest(BaseModel):
    """Request to record consent"""
    user_id: str


class ConsentResponse(BaseModel):
    """Consent status response"""
    user_id: str
    consent_status: bool
    consent_timestamp: Optional[datetime] = None


class AIConsentResponse(BaseModel):
    """AI consent status response"""
    user_id: str
    ai_consent_status: bool
    ai_consent_granted_at: Optional[datetime] = None


# Data & Analysis Models
class BehavioralProfileResponse(BaseModel):
    """Response for behavioral profile"""
    user_id: str
    persona: Optional[Dict[str, Any]] = None
    signals_30d: Optional[Dict[str, Any]] = None
    signals_180d: Optional[Dict[str, Any]] = None
    data_availability: str


class RecommendationItem(BaseModel):
    """Individual recommendation item"""
    recommendation_id: str
    title: str
    description: str
    type: str
    rationale: str
    persona_name: str
    operator_status: str
    generated_at: datetime


class RecommendationsResponse(BaseModel):
    """Response for recommendations"""
    user_id: str
    recommendations: List[RecommendationItem]
    total_count: int
    ai_used: bool = False
    ai_error_message: Optional[str] = None
    ai_model: Optional[str] = None
    ai_tokens_used: Optional[int] = None


class FeedbackRequest(BaseModel):
    """Request to submit feedback"""
    recommendation_id: str
    user_id: str
    thumbs_up: Optional[bool] = None
    helped_me: Optional[bool] = None
    applied_this: Optional[bool] = None
    free_text: Optional[str] = Field(None, max_length=200)


class FeedbackResponse(BaseModel):
    """Response after submitting feedback"""
    feedback_id: str
    message: str


# Operator Models
class ApprovalQueueItem(BaseModel):
    """Item in approval queue"""
    recommendation_id: str
    user_id: str
    title: str
    type: str
    rationale: str
    persona_name: str
    operator_status: str
    generated_at: datetime


class ApprovalQueueResponse(BaseModel):
    """Response for approval queue"""
    pending_count: int
    recommendations: List[ApprovalQueueItem]


class ApproveRequest(BaseModel):
    """Request to approve recommendation"""
    operator_notes: Optional[str] = None


class OverrideRequest(BaseModel):
    """Request to override recommendation"""
    custom_title: Optional[str] = None
    custom_description: Optional[str] = None
    custom_rationale: Optional[str] = None
    operator_notes: Optional[str] = None


class BulkApproveRequest(BaseModel):
    """Request for bulk approval"""
    persona_name: Optional[str] = None
    recommendation_ids: Optional[List[str]] = None
    operator_notes: Optional[str] = None


class OperatorResponse(BaseModel):
    """Generic operator action response"""
    success: bool
    message: str
    affected_count: int


# Evaluation Models
class EvaluationMetricsResponse(BaseModel):
    """Response for evaluation metrics"""
    scoring: Dict[str, Any]
    satisfaction: Dict[str, Any]
    fairness: Dict[str, Any]
    evaluation_date: str


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None

