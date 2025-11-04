"""Main recommendation engine"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
import sqlite3
import uuid
import json

from .models import Recommendation
from .catalog import EducationCatalog, EducationItem
from .offers import OfferGenerator, PartnerOffer
from .rationale import RationaleGenerator
from ..personas.assignment import PersonaAssigner
from ..features.aggregator import SignalAggregator
from ..features.degradation import GracefulDegradation
from ..guardrails.enforcer import GuardrailsEnforcer
from ..guardrails.ai_consent import AIConsentManager
from ..utils.logger import setup_logger
from ..utils.errors import DataError, ConsentError

logger = setup_logger(__name__)

# Import LLM generator after Recommendation class is defined
from .llm_generator import OpenAIGenerator, OpenAIAPIError


class RecommendationEngine:
    """Main recommendation generation engine"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize recommendation engine.
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
        self.aggregator = SignalAggregator(db_connection)
        self.degradation = GracefulDegradation(self.aggregator)
        self.persona_assigner = PersonaAssigner(db_connection)
        self.catalog = EducationCatalog()
        self.offer_generator = OfferGenerator(db_connection)
        self.rationale_generator = RationaleGenerator()
        self.guardrails = GuardrailsEnforcer(db_connection)
        self.llm_generator = OpenAIGenerator(db_connection)
        self.ai_consent_manager = AIConsentManager(db_connection)
    
    def generate_recommendations(
        self,
        user_id: str,
        num_education: int = 5,
        num_offers: int = 3,
        use_ai: bool = False
    ) -> Tuple[List[Recommendation], Dict[str, any]]:
        """Generate recommendations for a user.
        
        Args:
            user_id: User identifier
            num_education: Number of education items (default: 5)
            num_offers: Maximum number of offers (default: 3)
            use_ai: Whether to use AI for generation (default: False)
            
        Returns:
            Tuple of (recommendations list, metadata dictionary)
            Metadata includes: ai_used, error_message, etc.
        """
        # Get or assign persona
        assignment = self.persona_assigner.get_assignment(user_id)
        if not assignment:
            assignment = self.persona_assigner.assign_and_save(user_id)
        
        persona_name = assignment['persona_name']
        
        # Get signals
        signals = self.degradation.get_primary_signals(user_id)
        
        # Initialize metadata
        metadata = {
            "ai_used": False,
            "error_message": None,
            "model": None,
            "tokens_used": None
        }
        
        # Try AI generation if requested and consent granted
        if use_ai:
            try:
                # Check AI consent
                if not self.ai_consent_manager.check_ai_consent(user_id):
                    logger.warning(f"User {user_id} requested AI but does not have AI consent")
                    metadata["error_message"] = "AI consent required. Falling back to standard recommendations."
                else:
                    # Get user data for LLM prompt
                    user_data = self._get_user_data_summary(user_id)
                    
                    # Generate with LLM
                    try:
                        plan_document, recommendations, llm_metadata = self.llm_generator.generate_personalized_plan(
                            user_id, persona_name, signals, user_data, num_education, num_offers
                        )
                        
                        # Save AI plan
                        self.llm_generator.save_ai_plan(user_id, persona_name, plan_document, recommendations)
                        
                        # Update metadata
                        metadata.update(llm_metadata)
                        
                        logger.info(f"Successfully generated AI recommendations for user {user_id}")
                        
                        # Apply guardrails to AI recommendations
                        recommendations = self._apply_guardrails(user_id, recommendations, signals)
                        
                        return recommendations, metadata
                        
                    except OpenAIAPIError as e:
                        error_msg = f"AI generation failed: {str(e)}"
                        logger.warning(f"{error_msg} for user {user_id}. Falling back to static catalog.")
                        metadata["error_message"] = error_msg
                        # Fall through to static catalog generation
                        
            except Exception as e:
                error_msg = f"Unexpected error in AI generation: {str(e)}"
                logger.error(f"{error_msg} for user {user_id}. Falling back to static catalog.")
                metadata["error_message"] = error_msg
                # Fall through to static catalog generation
        
        # Fallback to static catalog (or default behavior)
        recommendations = []
        
        # Generate education recommendations
        education_items = self.catalog.get_education_items(persona_name, num_education)
        for item in education_items:
            rationale = self.rationale_generator.generate_education_rationale(
                item, signals, persona_name
            )
            
            recommendation = Recommendation(
                recommendation_id=str(uuid.uuid4()),
                user_id=user_id,
                persona_name=persona_name,
                type='education',
                title=item.title,
                rationale=rationale,
                generated_at=datetime.now().isoformat(),
                operator_status='pending'
            )
            recommendations.append(recommendation)
        
        # Generate partner offers
        offers = self.offer_generator.generate_offers(
            user_id, persona_name, signals, max_offers=num_offers
        )
        
        # Create mapping from offer titles to offer objects for later use
        offer_map = {}
        for offer in offers:
            rationale = self.rationale_generator.generate_offer_rationale(
                offer, signals, user_id
            )
            
            recommendation = Recommendation(
                recommendation_id=str(uuid.uuid4()),
                user_id=user_id,
                persona_name=persona_name,
                type='offer',
                title=offer.title,
                rationale=rationale,
                generated_at=datetime.now().isoformat(),
                operator_status='pending'
            )
            recommendations.append(recommendation)
            # Store offer object for guardrails
            offer_map[recommendation.recommendation_id] = offer
        
        logger.info(
            f"Generated {len(recommendations)} recommendations for user {user_id} "
            f"({len(education_items)} education, {len(offers)} offers)"
        )
        
        # Apply guardrails
        try:
            # Convert to dict format for guardrails
            rec_dicts = []
            for rec in recommendations:
                rec_dict = {
                    'recommendation_id': rec.recommendation_id,
                    'user_id': rec.user_id,
                    'persona_name': rec.persona_name,
                    'type': rec.type,
                    'title': rec.title,
                    'rationale': rec.rationale,
                    'generated_at': rec.generated_at,
                    'operator_status': rec.operator_status,
                }
                # Add offer_type if this is an offer
                if rec.type == 'offer' and rec.recommendation_id in offer_map:
                    rec_dict['offer_type'] = offer_map[rec.recommendation_id].offer_type
                else:
                    rec_dict['offer_type'] = ''
                rec_dicts.append(rec_dict)
            
            # Enforce guardrails
            filtered_recs = self.guardrails.enforce_guardrails(user_id, rec_dicts, signals)
            
            # Convert back to Recommendation objects
            filtered_recommendations = []
            for rec_dict in filtered_recs:
                rec = Recommendation(
                    recommendation_id=rec_dict['recommendation_id'],
                    user_id=rec_dict['user_id'],
                    persona_name=rec_dict['persona_name'],
                    type=rec_dict['type'],
                    title=rec_dict['title'],
                    rationale=rec_dict['rationale'],
                    generated_at=rec_dict['generated_at'],
                    operator_status=rec_dict['operator_status']
                )
                filtered_recommendations.append(rec)
            
            logger.info(
                f"Guardrails applied: {len(filtered_recommendations)}/{len(recommendations)} "
                f"recommendations passed"
            )
            
            return filtered_recommendations, metadata
            
        except ConsentError:
            logger.warning(f"User {user_id} does not have consent - returning empty recommendations")
            return [], metadata
    
    def save_recommendations(self, recommendations: List[Recommendation]):
        """Save recommendations to database.
        
        Args:
            recommendations: List of recommendations to save
        """
        cursor = self.conn.cursor()
        
        for rec in recommendations:
            cursor.execute("""
                INSERT OR REPLACE INTO recommendations (
                    recommendation_id, user_id, persona_name, type,
                    title, rationale, generated_at, operator_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rec.recommendation_id,
                rec.user_id,
                rec.persona_name,
                rec.type,
                rec.title,
                rec.rationale,
                rec.generated_at,
                rec.operator_status
            ))
        
        self.conn.commit()
        logger.debug(f"Saved {len(recommendations)} recommendations to database")
    
    def _get_user_data_summary(self, user_id: str) -> Dict[str, any]:
        """Get user account and transaction summary for LLM prompt.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with account summary data
        """
        cursor = self.conn.cursor()
        
        # Get account counts
        cursor.execute("""
            SELECT 
                COUNT(*) as account_count,
                SUM(CASE WHEN type IN ('depository', 'checking', 'savings') THEN 1 ELSE 0 END) as deposit_accounts,
                SUM(CASE WHEN type IN ('credit', 'credit card') THEN 1 ELSE 0 END) as credit_accounts,
                SUM(COALESCE(balance_current, balance_available, 0)) as total_balance
            FROM accounts
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        
        if result:
            return {
                'account_count': result['account_count'] or 0,
                'deposit_accounts': result['deposit_accounts'] or 0,
                'credit_accounts': result['credit_accounts'] or 0,
                'total_balance': float(result['total_balance'] or 0)
            }
        else:
            return {
                'account_count': 0,
                'deposit_accounts': 0,
                'credit_accounts': 0,
                'total_balance': 0.0
            }
    
    def _apply_guardrails(self, user_id: str, recommendations: List[Recommendation], signals: Dict[str, any]) -> List[Recommendation]:
        """Apply guardrails to recommendations.
        
        Args:
            user_id: User identifier
            recommendations: List of recommendations
            signals: Behavioral signals
            
        Returns:
            Filtered list of recommendations that pass guardrails
        """
        try:
            # Convert to dict format for guardrails
            rec_dicts = []
            for rec in recommendations:
                rec_dict = {
                    'recommendation_id': rec.recommendation_id,
                    'user_id': rec.user_id,
                    'persona_name': rec.persona_name,
                    'type': rec.type,
                    'title': rec.title,
                    'rationale': rec.rationale,
                    'generated_at': rec.generated_at,
                    'operator_status': rec.operator_status,
                    'offer_type': ''  # AI recommendations don't have offer_type
                }
                rec_dicts.append(rec_dict)
            
            # Enforce guardrails
            filtered_recs = self.guardrails.enforce_guardrails(user_id, rec_dicts, signals)
            
            # Convert back to Recommendation objects
            filtered_recommendations = []
            for rec_dict in filtered_recs:
                rec = Recommendation(
                    recommendation_id=rec_dict['recommendation_id'],
                    user_id=rec_dict['user_id'],
                    persona_name=rec_dict['persona_name'],
                    type=rec_dict['type'],
                    title=rec_dict['title'],
                    rationale=rec_dict['rationale'],
                    generated_at=rec_dict['generated_at'],
                    operator_status=rec_dict['operator_status']
                )
                # Add description if present (for AI-generated recommendations)
                if 'description' in rec_dict:
                    rec.description = rec_dict['description']
                filtered_recommendations.append(rec)
            
            return filtered_recommendations
            
        except Exception as e:
            logger.warning(f"Error applying guardrails: {e}. Returning all recommendations.")
            return recommendations
    
    def generate_and_save(self, user_id: str, use_ai: bool = False) -> Tuple[List[Recommendation], Dict[str, any]]:
        """Generate recommendations and save to database in one operation.
        
        Args:
            user_id: User identifier
            use_ai: Whether to use AI for generation (default: False)
            
        Returns:
            Tuple of (recommendations list, metadata dictionary)
        """
        recommendations, metadata = self.generate_recommendations(user_id, use_ai=use_ai)
        self.save_recommendations(recommendations)
        return recommendations, metadata
    
    def get_recommendations(self, user_id: str) -> List[Dict[str, any]]:
        """Get stored recommendations for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of recommendation dictionaries
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT recommendation_id, persona_name, type, title, rationale,
                   generated_at, operator_status
            FROM recommendations
            WHERE user_id = ?
            ORDER BY type, generated_at DESC
        """, (user_id,))
        
        results = cursor.fetchall()
        
        return [
            {
                'recommendation_id': row['recommendation_id'],
                'persona_name': row['persona_name'],
                'type': row['type'],
                'title': row['title'],
                'rationale': row['rationale'],
                'generated_at': row['generated_at'],
                'operator_status': row['operator_status']
            }
            for row in results
        ]

