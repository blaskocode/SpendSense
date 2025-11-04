"""Approval queue and recommendation management"""

from typing import List, Dict, Optional
from datetime import datetime
import sqlite3

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ApprovalManager:
    """Manages recommendation approval queue"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize approval manager.
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
    
    def get_approval_queue(
        self,
        persona_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, any]]:
        """Get pending recommendations requiring approval.
        
        Args:
            persona_name: Filter by persona name (optional)
            limit: Maximum number of results
            
        Returns:
            List of pending recommendation dictionaries
        """
        cursor = self.conn.cursor()
        
        query = """
            SELECT r.recommendation_id, r.user_id, r.persona_name, r.type,
                   r.title, r.rationale, r.generated_at,
                   u.consent_status, p.priority_level
            FROM recommendations r
            JOIN users u ON r.user_id = u.user_id
            LEFT JOIN personas p ON r.user_id = p.user_id
            WHERE r.operator_status = 'pending'
        """
        params = []
        
        if persona_name:
            query += " AND r.persona_name = ?"
            params.append(persona_name)
        
        query += " ORDER BY r.generated_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        return [
            {
                'recommendation_id': row['recommendation_id'],
                'user_id': row['user_id'],
                'persona_name': row['persona_name'],
                'priority_level': row['priority_level'],
                'type': row['type'],
                'title': row['title'],
                'rationale': row['rationale'],
                'generated_at': row['generated_at'],
                'consent_status': bool(row['consent_status'])
            }
            for row in results
        ]
    
    def approve_recommendation(
        self,
        recommendation_id: str,
        operator_notes: Optional[str] = None
    ) -> bool:
        """Approve a recommendation.
        
        Args:
            recommendation_id: Recommendation identifier
            operator_notes: Optional operator notes
            
        Returns:
            True if approved successfully
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            UPDATE recommendations
            SET operator_status = 'approved',
                generated_at = ?
            WHERE recommendation_id = ?
        """, (datetime.now().isoformat(), recommendation_id))
        
        if cursor.rowcount == 0:
            return False
        
        self.conn.commit()
        logger.info(f"Approved recommendation {recommendation_id}")
        
        return True
    
    def override_recommendation(
        self,
        recommendation_id: str,
        custom_title: str,
        custom_rationale: str,
        operator_notes: Optional[str] = None
    ) -> bool:
        """Override a recommendation with custom content.
        
        Args:
            recommendation_id: Recommendation identifier
            custom_title: Custom recommendation title
            custom_rationale: Custom recommendation rationale
            operator_notes: Optional operator notes
            
        Returns:
            True if overridden successfully
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            UPDATE recommendations
            SET operator_status = 'overridden',
                title = ?,
                rationale = ?,
                generated_at = ?
            WHERE recommendation_id = ?
        """, (
            custom_title,
            custom_rationale,
            datetime.now().isoformat(),
            recommendation_id
        ))
        
        if cursor.rowcount == 0:
            return False
        
        self.conn.commit()
        logger.info(f"Overridden recommendation {recommendation_id}")
        
        return True
    
    def bulk_approve_by_persona(
        self,
        persona_name: str,
        operator_notes: Optional[str] = None
    ) -> int:
        """Bulk approve all pending recommendations for a persona.
        
        Args:
            persona_name: Persona name
            operator_notes: Optional operator notes
            
        Returns:
            Number of recommendations approved
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            UPDATE recommendations
            SET operator_status = 'approved',
                generated_at = ?
            WHERE persona_name = ? AND operator_status = 'pending'
        """, (datetime.now().isoformat(), persona_name))
        
        count = cursor.rowcount
        self.conn.commit()
        
        logger.info(f"Bulk approved {count} recommendations for persona {persona_name}")
        
        return count
    
    def bulk_approve_selected(
        self,
        recommendation_ids: List[str],
        operator_notes: Optional[str] = None
    ) -> int:
        """Bulk approve selected recommendations.
        
        Args:
            recommendation_ids: List of recommendation IDs
            operator_notes: Optional operator notes
            
        Returns:
            Number of recommendations approved
        """
        if not recommendation_ids:
            return 0
        
        cursor = self.conn.cursor()
        
        placeholders = ','.join('?' * len(recommendation_ids))
        query = f"""
            UPDATE recommendations
            SET operator_status = 'approved',
                generated_at = ?
            WHERE recommendation_id IN ({placeholders})
              AND operator_status = 'pending'
        """
        
        params = [datetime.now().isoformat()] + recommendation_ids
        
        cursor.execute(query, params)
        count = cursor.rowcount
        self.conn.commit()
        
        logger.info(f"Bulk approved {count} selected recommendations")
        
        return count
    
    def flag_for_review(
        self,
        recommendation_id: str,
        operator_notes: Optional[str] = None
    ) -> bool:
        """Flag a recommendation for manual review.
        
        Args:
            recommendation_id: Recommendation identifier
            operator_notes: Optional operator notes
            
        Returns:
            True if flagged successfully
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            UPDATE recommendations
            SET operator_status = 'flagged',
                generated_at = ?
            WHERE recommendation_id = ?
        """, (datetime.now().isoformat(), recommendation_id))
        
        if cursor.rowcount == 0:
            return False
        
        self.conn.commit()
        logger.info(f"Flagged recommendation {recommendation_id} for review")
        
        return True

