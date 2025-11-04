"""LLM-powered recommendation generator using OpenAI"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import uuid
import sqlite3

from openai import OpenAI
from openai import APIError, APITimeoutError, RateLimitError

from ..utils.config import (
    OPENAI_API_KEY, OPENAI_MODEL, OPENAI_MAX_TOKENS,
    OPENAI_TIMEOUT, OPENAI_TEMPERATURE
)
from ..utils.logger import setup_logger
from ..utils.errors import DataError
from .prompts import build_financial_plan_prompt, build_offer_recommendations_prompt
from .models import Recommendation

logger = setup_logger(__name__)


class OpenAIAPIError(Exception):
    """Custom exception for OpenAI API errors"""
    pass


class OpenAIGenerator:
    """Generates personalized financial plans using OpenAI GPT"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize OpenAI generator.
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
        
        if not OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not set. LLM features will not work.")
            self.client = None
        else:
            self.client = OpenAI(api_key=OPENAI_API_KEY)
        
        self.model = OPENAI_MODEL
        self.max_tokens = OPENAI_MAX_TOKENS
        self.timeout = OPENAI_TIMEOUT
        self.temperature = OPENAI_TEMPERATURE
    
    def generate_personalized_plan(
        self,
        user_id: str,
        persona_name: str,
        signals: Dict[str, Any],
        user_data: Dict[str, Any],
        num_education: int = 5,
        num_offers: int = 3
    ) -> Tuple[Dict[str, Any], List[Recommendation], Dict[str, Any]]:
        """Generate personalized financial plan using OpenAI.
        
        Args:
            user_id: User identifier
            persona_name: Assigned persona name
            signals: Behavioral signals dictionary
            user_data: User account and transaction summary
            num_education: Number of education recommendations (default: 5)
            num_offers: Number of offer recommendations (default: 3)
            
        Returns:
            Tuple of (plan_document, recommendations, metadata)
            
        Raises:
            OpenAIAPIError: If API call fails
        """
        if not self.client:
            raise OpenAIAPIError("OpenAI API key not configured")
        
        try:
            # Build prompt
            prompt = build_financial_plan_prompt(persona_name, signals, user_data)
            
            logger.info(f"Calling OpenAI API for user {user_id} with model {self.model}")
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial advisor helping users create personalized financial plans. Always respond with valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout
            )
            
            # Extract response
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else None
            
            logger.info(f"OpenAI API call successful for user {user_id}. Tokens used: {tokens_used}")
            
            # Parse JSON response
            plan_data = self._parse_llm_response(content)
            
            # Convert to recommendations
            recommendations = self._convert_to_recommendations(
                user_id, persona_name, plan_data, num_education, num_offers
            )
            
            # Build plan document
            plan_document = {
                "plan_summary": plan_data.get("plan_summary", ""),
                "key_insights": plan_data.get("key_insights", []),
                "action_items": plan_data.get("action_items", []),
                "generated_at": datetime.now().isoformat(),
                "model_used": self.model,
                "tokens_used": tokens_used
            }
            
            metadata = {
                "ai_used": True,
                "model": self.model,
                "tokens_used": tokens_used,
                "error_message": None
            }
            
            return plan_document, recommendations, metadata
            
        except APITimeoutError as e:
            error_msg = f"OpenAI API timeout after {self.timeout} seconds"
            logger.error(f"{error_msg} for user {user_id}: {e}")
            raise OpenAIAPIError(error_msg) from e
        
        except RateLimitError as e:
            error_msg = "OpenAI API rate limit exceeded"
            logger.error(f"{error_msg} for user {user_id}: {e}")
            raise OpenAIAPIError(error_msg) from e
        
        except APIError as e:
            error_msg = f"OpenAI API error: {str(e)}"
            logger.error(f"{error_msg} for user {user_id}: {e}")
            raise OpenAIAPIError(error_msg) from e
        
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse OpenAI response as JSON: {str(e)}"
            logger.error(f"{error_msg} for user {user_id}")
            raise OpenAIAPIError(error_msg) from e
        
        except Exception as e:
            error_msg = f"Unexpected error in OpenAI API call: {str(e)}"
            logger.error(f"{error_msg} for user {user_id}: {e}")
            raise OpenAIAPIError(error_msg) from e
    
    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response content.
        
        Args:
            content: Raw response from OpenAI
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            OpenAIAPIError: If parsing fails
        """
        # Try to extract JSON from markdown code blocks if present
        content = content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]  # Remove ```json
        elif content.startswith("```"):
            content = content[3:]  # Remove ```
        
        if content.endswith("```"):
            content = content[:-3]  # Remove trailing ```
        
        content = content.strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {content[:200]}")
            raise OpenAIAPIError(f"Invalid JSON response from OpenAI: {str(e)}") from e
    
    def _convert_to_recommendations(
        self,
        user_id: str,
        persona_name: str,
        plan_data: Dict[str, Any],
        num_education: int,
        num_offers: int
    ) -> List[Recommendation]:
        """Convert LLM plan data to Recommendation objects.
        
        Args:
            user_id: User identifier
            persona_name: Persona name
            plan_data: Parsed plan data from LLM
            num_education: Target number of education recommendations
            num_offers: Target number of offer recommendations
            
        Returns:
            List of Recommendation objects
        """
        recommendations = []
        
        # Extract recommendations from plan data
        plan_recommendations = plan_data.get("recommendations", [])
        
        # Separate education and offers
        education_items = [r for r in plan_recommendations if r.get("type") == "education"]
        offer_items = [r for r in plan_recommendations if r.get("type") == "offer"]
        
        # Limit to requested counts
        education_items = education_items[:num_education]
        offer_items = offer_items[:num_offers]
        
        # Convert to Recommendation objects
        for item in education_items + offer_items:
            # Store description in recommendation data for later retrieval
            description = item.get("description", "")
            title = item.get("title", "")
            rationale = item.get("rationale", "")
            
            recommendation = Recommendation(
                recommendation_id=str(uuid.uuid4()),
                user_id=user_id,
                persona_name=persona_name,
                type=item.get("type", "education"),
                title=title,
                rationale=rationale,
                generated_at=datetime.now().isoformat(),
                operator_status='pending'
            )
            # Store description as an attribute for API response
            recommendation.description = description
            recommendations.append(recommendation)
        
        return recommendations
    
    def save_ai_plan(
        self,
        user_id: str,
        persona_name: str,
        plan_document: Dict[str, Any],
        recommendations: List[Recommendation]
    ) -> str:
        """Save AI-generated plan to database.
        
        Args:
            user_id: User identifier
            persona_name: Persona name
            plan_document: Plan document dictionary
            recommendations: List of recommendations
            
        Returns:
            Plan ID
        """
        plan_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        
        # Convert recommendations to JSON
        recommendations_json = json.dumps([
            {
                "recommendation_id": r.recommendation_id,
                "type": r.type,
                "title": r.title,
                "rationale": r.rationale
            }
            for r in recommendations
        ])
        
        # Save plan
        cursor.execute("""
            INSERT OR REPLACE INTO ai_plans (
                plan_id, user_id, persona_name, plan_document,
                recommendations, generated_at, model_used, tokens_used
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            plan_id,
            user_id,
            persona_name,
            json.dumps(plan_document),
            recommendations_json,
            datetime.now().isoformat(),
            plan_document.get("model_used"),
            plan_document.get("tokens_used")
        ))
        
        self.conn.commit()
        logger.debug(f"Saved AI plan {plan_id} for user {user_id}")
        
        return plan_id
    
    def get_ai_plan(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve AI-generated plan for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Plan document dictionary or None if not found
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT plan_id, persona_name, plan_document, recommendations,
                   generated_at, model_used, tokens_used
            FROM ai_plans
            WHERE user_id = ?
            ORDER BY generated_at DESC
            LIMIT 1
        """, (user_id,))
        
        result = cursor.fetchone()
        
        if result:
            plan_document = json.loads(result['plan_document'])
            recommendations = json.loads(result['recommendations'])
            
            return {
                "plan_id": result['plan_id'],
                "persona_name": result['persona_name'],
                "plan_document": plan_document,
                "recommendations": recommendations,
                "generated_at": result['generated_at'],
                "model_used": result['model_used'],
                "tokens_used": result['tokens_used']
            }
        
        return None

