"""Main recommendation engine"""

from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass
import sqlite3
import uuid
import json

from .catalog import EducationCatalog, EducationItem
from .offers import OfferGenerator, PartnerOffer
from .rationale import RationaleGenerator
from ..personas.assignment import PersonaAssigner
from ..features.aggregator import SignalAggregator
from ..features.degradation import GracefulDegradation
from ..guardrails.enforcer import GuardrailsEnforcer
from ..utils.logger import setup_logger
from ..utils.errors import DataError, ConsentError

logger = setup_logger(__name__)


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
    
    def generate_recommendations(
        self,
        user_id: str,
        num_education: int = 5,
        num_offers: int = 3
    ) -> List[Recommendation]:
        """Generate recommendations for a user.
        
        Args:
            user_id: User identifier
            num_education: Number of education items (default: 5)
            num_offers: Maximum number of offers (default: 3)
            
        Returns:
            List of recommendations
        """
        # Get or assign persona
        assignment = self.persona_assigner.get_assignment(user_id)
        if not assignment:
            assignment = self.persona_assigner.assign_and_save(user_id)
        
        persona_name = assignment['persona_name']
        
        # Get signals
        signals = self.degradation.get_primary_signals(user_id)
        
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
            
            return filtered_recommendations
            
        except ConsentError:
            logger.warning(f"User {user_id} does not have consent - returning empty recommendations")
            return []
    
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
    
    def generate_and_save(self, user_id: str) -> List[Recommendation]:
        """Generate recommendations and save to database in one operation.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of recommendations
        """
        recommendations = self.generate_recommendations(user_id)
        self.save_recommendations(recommendations)
        return recommendations
    
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

