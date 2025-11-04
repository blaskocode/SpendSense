"""Data & analysis API routes"""

from datetime import datetime, date, timedelta
from fastapi import APIRouter, HTTPException

from ..storage.sqlite_manager import SQLiteManager
from ..operator.review import UserReviewer
from ..recommend.engine import RecommendationEngine
from ..ui.feedback import FeedbackCollector
from ..utils.logger import setup_logger
from ..utils.config import TODAY
from .models import (
    BehavioralProfileResponse,
    RecommendationsResponse, RecommendationItem,
    FeedbackRequest, FeedbackResponse,
    ErrorResponse
)

logger = setup_logger(__name__)
router = APIRouter(prefix="/data", tags=["Data & Analysis"])


def get_db():
    """Get database connection"""
    db_manager = SQLiteManager()
    db_manager.connect()
    return db_manager


@router.get("/profile/{user_id}", response_model=BehavioralProfileResponse)
def get_profile(user_id: str):
    """Get behavioral profile for a user (signals, persona)."""
    db_manager = get_db()
    
    try:
        user_reviewer = UserReviewer(db_manager.conn)
        profile = user_reviewer.get_user_profile(user_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile not found for user {user_id}")
        
        return BehavioralProfileResponse(
            user_id=profile['user_id'],
            persona=profile['persona'],
            signals_30d=profile['signals_30d'],
            signals_180d=profile['signals_180d'],
            data_availability=profile['data_availability']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_manager.close()


@router.get("/recommendations/{user_id}", response_model=RecommendationsResponse)
def get_recommendations(user_id: str, use_ai: bool = False):
    """Get recommendations for a user.
    
    If no recommendations exist, generates them automatically.
    
    Args:
        user_id: User identifier
        use_ai: Whether to use AI for generation (default: False)
    """
    db_manager = get_db()
    
    try:
        recommendation_engine = RecommendationEngine(db_manager.conn)
        
        # Check if recommendations exist, if not, generate them
        stored_recommendations = recommendation_engine.get_recommendations(user_id)
        
        if not stored_recommendations or use_ai:
            # No recommendations found or AI requested, generate them
            logger.info(f"Generating recommendations for {user_id} (use_ai={use_ai})...")
            recommendations, metadata = recommendation_engine.generate_and_save(user_id, use_ai=use_ai)
            
            # Convert Recommendation objects to dicts
            recommendations = [
                {
                    'recommendation_id': rec.recommendation_id,
                    'persona_name': rec.persona_name,
                    'type': rec.type,
                    'title': rec.title,
                    'description': getattr(rec, 'description', ''),
                    'rationale': rec.rationale,
                    'operator_status': rec.operator_status,
                    'generated_at': datetime.now().isoformat()
                }
                for rec in recommendations
            ]
            
            # Store metadata for response (will be added to response model later)
            ai_metadata = metadata
        else:
            # Use stored recommendations
            recommendations = stored_recommendations
            ai_metadata = {"ai_used": False, "error_message": None}
        
        # Limit recommendations to PRD spec: 3-5 education, 1-3 offers
        education_items = [r for r in recommendations if r.get('type') == 'education']
        offer_items = [r for r in recommendations if r.get('type') == 'offer']
        
        # Deduplicate by title (keep first occurrence)
        seen_education_titles = set()
        unique_education = []
        for item in education_items:
            title = item.get('title', '')
            if title and title not in seen_education_titles:
                seen_education_titles.add(title)
                unique_education.append(item)
        
        seen_offer_titles = set()
        unique_offers = []
        for item in offer_items:
            title = item.get('title', '')
            if title and title not in seen_offer_titles:
                seen_offer_titles.add(title)
                unique_offers.append(item)
        
        # Limit to 5 education and 3 offers maximum (after deduplication)
        education_items = unique_education[:5]
        offer_items = unique_offers[:3]
        
        # Combine and maintain order (education first, then offers)
        limited_recommendations = education_items + offer_items
        
        # Convert to response model
        items = []
        for rec in limited_recommendations:
            try:
                # Handle both dict and object formats
                if isinstance(rec, dict):
                    rec_id = rec['recommendation_id']
                    rec_title = rec['title']
                    rec_type = rec['type']
                    rec_rationale = rec.get('rationale', '')
                    rec_persona = rec.get('persona_name', '')
                    rec_status = rec.get('operator_status', 'pending')
                    rec_generated = rec.get('generated_at', datetime.now().isoformat())
                else:
                    # Handle Recommendation object
                    rec_id = rec.recommendation_id
                    rec_title = rec.title
                    rec_type = rec.type
                    rec_rationale = rec.rationale
                    rec_persona = rec.persona_name
                    rec_status = rec.operator_status
                    rec_generated = rec.generated_at if hasattr(rec, 'generated_at') else datetime.now().isoformat()
                
                # Parse generated_at if it's a string
                if isinstance(rec_generated, str):
                    try:
                        generated_at = datetime.fromisoformat(rec_generated.replace('Z', '+00:00'))
                    except:
                        generated_at = datetime.fromisoformat(rec_generated)
                else:
                    generated_at = rec_generated
                
                # Get description from recommendation data if available (for AI-generated recommendations)
                rec_description = ''
                if isinstance(rec, dict) and 'description' in rec:
                    rec_description = rec.get('description', '')
                
                items.append(RecommendationItem(
                    recommendation_id=rec_id,
                    title=rec_title,
                    description=rec_description,
                    type=rec_type,
                    rationale=rec_rationale,
                    persona_name=rec_persona,
                    operator_status=rec_status,
                    generated_at=generated_at
                ))
            except Exception as e:
                logger.error(f"Error converting recommendation to item: {e}, rec: {rec}")
                continue
        
        logger.info(f"Returning {len(items)} recommendations for user {user_id}")
        return RecommendationsResponse(
            user_id=user_id,
            recommendations=items,
            total_count=len(items),
            ai_used=ai_metadata.get("ai_used", False),
            ai_error_message=ai_metadata.get("error_message"),
            ai_model=ai_metadata.get("model"),
            ai_tokens_used=ai_metadata.get("tokens_used")
        )
    
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_manager.close()


@router.get("/ai-plan/{user_id}")
def get_ai_plan(user_id: str):
    """Retrieve AI-generated plan for a user.
    
    Args:
        user_id: User identifier
        
    Returns:
        AI-generated plan document
    """
    db_manager = get_db()
    
    try:
        from ..recommend.llm_generator import OpenAIGenerator
        
        llm_generator = OpenAIGenerator(db_manager.conn)
        plan = llm_generator.get_ai_plan(user_id)
        
        if not plan:
            raise HTTPException(
                status_code=404,
                detail=f"No AI-generated plan found for user {user_id}"
            )
        
        return plan
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_manager.close()


@router.get("/transactions/{user_id}")
def get_transactions(user_id: str, limit: int = 50, offset: int = 0, start_date: str = None, end_date: str = None):
    """Get transaction records for a user.
    
    Args:
        user_id: User identifier
        limit: Maximum number of transactions to return (default: 50, use 0 for no limit)
        offset: Number of transactions to skip for pagination (default: 0)
        start_date: Start date for filtering (YYYY-MM-DD format, optional)
        end_date: End date for filtering (YYYY-MM-DD format, optional)
    """
    db_manager = get_db()
    
    try:
        cursor = db_manager.conn.cursor()
        
        # Build query with optional date filtering
        query = """
            SELECT 
                t.transaction_id,
                t.account_id,
                a.type as account_type,
                a.subtype as account_subtype,
                t.date,
                t.amount,
                t.merchant_name,
                t.merchant_entity_id,
                COALESCE(t.category_primary, t.category_detailed, 'Uncategorized') as category,
                t.category_primary,
                t.category_detailed,
                t.pending,
                t.payment_channel
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.user_id = ?
        """
        params = [user_id]
        
        # Add date filtering if provided
        if start_date:
            query += " AND t.date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND t.date <= ?"
            params.append(end_date)
        
        query += " ORDER BY t.date DESC, t.transaction_id DESC"
        
        # Add limit/offset if limit is specified and > 0
        if limit and limit > 0:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        cursor.execute(query, tuple(params))
        
        transactions = cursor.fetchall()
        
        # Get total count for pagination (with same date filters)
        count_query = """
            SELECT COUNT(*) as count
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.user_id = ?
        """
        count_params = [user_id]
        
        if start_date:
            count_query += " AND t.date >= ?"
            count_params.append(start_date)
        if end_date:
            count_query += " AND t.date <= ?"
            count_params.append(end_date)
        
        cursor.execute(count_query, tuple(count_params))
        total_count = cursor.fetchone()['count']
        
        # Build transaction list
        transaction_list = []
        for row in transactions:
            # Build account name from subtype or type
            account_subtype = row['account_subtype']
            account_type = row['account_type']
            if account_subtype:
                account_name = f"{account_subtype} Account"
            elif account_type:
                account_name = f"{account_type} Account"
            else:
                account_name = "Account"
            
            transaction_list.append({
                "transaction_id": row['transaction_id'],
                "account_id": row['account_id'],
                "account_type": account_type or 'Unknown',
                "account_subtype": account_subtype or None,
                "account_name": account_name,
                "date": row['date'],
                "amount": float(row['amount']),
                "merchant_name": row['merchant_name'] or 'Unknown',
                "merchant_entity_id": row['merchant_entity_id'] or None,
                "category": row['category'] or 'Uncategorized',
                "category_primary": row['category_primary'] or None,
                "category_detailed": row['category_detailed'] or None,
                "pending": bool(row['pending']),
                "payment_channel": row['payment_channel'] or 'Unknown'
            })
        
        return {
            "user_id": user_id,
            "transactions": transaction_list,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
    
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_manager.close()


@router.get("/subscriptions/{user_id}")
def get_subscriptions(user_id: str):
    """Get active subscriptions for a user.
    
    Args:
        user_id: User identifier
    """
    db_manager = get_db()
    
    try:
        cursor = db_manager.conn.cursor()
        
        # Get all subscription transactions using EXACT same logic as SubscriptionDetector:
        # 1. Use same date range as TimeWindowPartitioner: [today-30, today-1] (EXCLUDE today)
        # 2. EXCLUDE pending transactions (matching windowing exclude_pending=True)
        # 3. Find ALL merchants with ≥3 transactions where span ≤90 days
        # This ensures the count EXACTLY matches what users see in the Behavioral Insights section
        
        # Calculate dates exactly like TimeWindowPartitioner.get_30_day_window()
        end_date = TODAY - timedelta(days=1)      # Exclude today (matching windowing)
        start_date = end_date - timedelta(days=29)  # 30 days total (inclusive)
        
        cursor.execute("""
            SELECT 
                a.user_id,
                t.merchant_name,
                t.category_primary,
                t.category_detailed,
                COUNT(*) as transaction_count,
                AVG(ABS(t.amount)) as avg_amount,
                MIN(t.date) as first_transaction,
                MAX(t.date) as last_transaction,
                JULIANDAY(MAX(t.date)) - JULIANDAY(MIN(t.date)) as day_span
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.user_id = ?
              AND t.date >= ?  -- Start date: today-30 (matching windowing)
              AND t.date <= ?  -- End date: today-1 (EXCLUDE today, matching windowing)
              AND t.pending = 0  -- EXCLUDE pending transactions (matching windowing)
              AND t.amount < 0  -- Only count negative transactions (debits/spending)
              AND t.merchant_name IS NOT NULL  -- Must have a merchant name
            GROUP BY a.user_id, t.merchant_name
            HAVING COUNT(*) >= 3  -- Require ≥3 transactions in window
               AND day_span <= 90  -- First to last transaction within 90-day window (matching SubscriptionDetector)
            ORDER BY avg_amount DESC  -- Show most expensive subscriptions first
        """, [user_id, start_date, end_date])
        
        subscriptions_data = cursor.fetchall()
        
        # Build subscription list
        # All subscriptions returned from query are already active (filtered in SQL)
        subscriptions = []
        for row in subscriptions_data:
            subscriptions.append({
                "merchant_name": row['merchant_name'],
                "category": row['category_primary'] or 'Entertainment',
                "avg_monthly_cost": float(row['avg_amount']),
                "transaction_count": row['transaction_count'],
                "first_transaction": row['first_transaction'],
                "last_transaction": row['last_transaction'],
                "is_active": True  # All subscriptions in this list are active (filtered in SQL)
            })
        
        # Calculate total monthly cost for active subscriptions only
        total_monthly_cost = sum(sub['avg_monthly_cost'] for sub in subscriptions)
        
        return {
            "user_id": user_id,
            "subscriptions": subscriptions,
            "total_count": len(subscriptions),
            "total_monthly_cost": total_monthly_cost
        }
    
    except Exception as e:
        logger.error(f"Error getting subscriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_manager.close()


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(request: FeedbackRequest):
    """Submit feedback on a recommendation."""
    db_manager = get_db()
    
    try:
        feedback_collector = FeedbackCollector(db_manager.conn)
        
        feedback_id = feedback_collector.submit_feedback(
            recommendation_id=request.recommendation_id,
            user_id=request.user_id,
            thumbs_up=request.thumbs_up,
            helped_me=request.helped_me,
            applied_this=request.applied_this,
            free_text=request.free_text
        )
        
        return FeedbackResponse(
            feedback_id=feedback_id,
            message="Feedback submitted successfully"
        )
    
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_manager.close()

