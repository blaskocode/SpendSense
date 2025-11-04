"""Operator API routes"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from ..storage.sqlite_manager import SQLiteManager
from ..operator.review import UserReviewer
from ..operator.approval import ApprovalManager
from ..operator.analytics import AnalyticsManager
from ..operator.feedback_review import FeedbackReviewer
from ..utils.logger import setup_logger
from .models import (
    ApprovalQueueResponse, ApprovalQueueItem,
    ApproveRequest, OverrideRequest, BulkApproveRequest,
    OperatorResponse,
    ErrorResponse
)

logger = setup_logger(__name__)
router = APIRouter(prefix="/operator", tags=["Operator"])


def get_db():
    """Get database connection"""
    db_manager = SQLiteManager()
    db_manager.connect()
    return db_manager


@router.get("/review", response_model=ApprovalQueueResponse)
def get_approval_queue():
    """Get approval queue of pending recommendations."""
    db_manager = get_db()
    
    try:
        approval_manager = ApprovalManager(db_manager.conn)
        queue = approval_manager.get_pending_queue()
        
        items = [
            ApprovalQueueItem(
                recommendation_id=rec['recommendation_id'],
                user_id=rec['user_id'],
                title=rec['title'],
                type=rec['type'],
                rationale=rec['rationale'],
                persona_name=rec['persona_name'],
                operator_status=rec['operator_status'],
                generated_at=rec['generated_at']
            )
            for rec in queue
        ]
        
        return ApprovalQueueResponse(
            pending_count=len(items),
            recommendations=items
        )
    
    except Exception as e:
        logger.error(f"Error getting approval queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_manager.close()


@router.post("/approve/{recommendation_id}", response_model=OperatorResponse)
def approve_recommendation(recommendation_id: str, request: ApproveRequest):
    """Approve a recommendation."""
    db_manager = get_db()
    
    try:
        approval_manager = ApprovalManager(db_manager.conn)
        approval_manager.approve_recommendation(
            recommendation_id=recommendation_id,
            operator_notes=request.operator_notes
        )
        
        return OperatorResponse(
            success=True,
            message=f"Recommendation {recommendation_id} approved",
            affected_count=1
        )
    
    except Exception as e:
        logger.error(f"Error approving recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_manager.close()


@router.post("/override/{recommendation_id}", response_model=OperatorResponse)
def override_recommendation(recommendation_id: str, request: OverrideRequest):
    """Override a recommendation with custom content."""
    db_manager = get_db()
    
    try:
        approval_manager = ApprovalManager(db_manager.conn)
        approval_manager.override_recommendation(
            recommendation_id=recommendation_id,
            custom_title=request.custom_title,
            custom_description=request.custom_description,
            custom_rationale=request.custom_rationale,
            operator_notes=request.operator_notes
        )
        
        return OperatorResponse(
            success=True,
            message=f"Recommendation {recommendation_id} overridden",
            affected_count=1
        )
    
    except Exception as e:
        logger.error(f"Error overriding recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_manager.close()


@router.post("/bulk_approve", response_model=OperatorResponse)
def bulk_approve(request: BulkApproveRequest):
    """Bulk approve recommendations."""
    db_manager = get_db()
    
    try:
        approval_manager = ApprovalManager(db_manager.conn)
        
        if request.recommendation_ids:
            count = approval_manager.bulk_approve_by_ids(
                recommendation_ids=request.recommendation_ids,
                operator_notes=request.operator_notes
            )
            message = f"Approved {count} recommendations"
        elif request.persona_name:
            count = approval_manager.bulk_approve_by_persona(
                persona_name=request.persona_name,
                operator_notes=request.operator_notes
            )
            message = f"Approved {count} recommendations for persona {request.persona_name}"
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide either recommendation_ids or persona_name"
            )
        
        return OperatorResponse(
            success=True,
            message=message,
            affected_count=count
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk approving: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_manager.close()


@router.get("/analytics")
def get_analytics():
    """Get system analytics and metrics."""
    db_manager = get_db()
    
    try:
        analytics = AnalyticsManager(db_manager.conn)
        return analytics.get_all_analytics()
    
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_manager.close()


@router.get("/feedback")
def get_feedback_aggregated():
    """Get aggregated user feedback."""
    db_manager = get_db()
    
    try:
        feedback_reviewer = FeedbackReviewer(db_manager.conn)
        return feedback_reviewer.get_aggregated_feedback()
    
    except Exception as e:
        logger.error(f"Error getting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_manager.close()

