"""Persona assignment orchestrator"""

from typing import Dict, Optional
from datetime import datetime
import sqlite3
import json

from .criteria import Persona, PersonaMatcher
from .prioritization import PersonaPrioritizer
from ..features.aggregator import SignalAggregator
from ..features.degradation import GracefulDegradation
from ..utils.logger import setup_logger
from ..utils.errors import DataError

logger = setup_logger(__name__)


class PersonaAssigner:
    """Assigns primary persona to users based on behavioral signals"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize persona assigner.
        
        Args:
            db_connection: SQLite database connection
        """
        self.conn = db_connection
        self.aggregator = SignalAggregator(db_connection)
        self.degradation = GracefulDegradation(self.aggregator)
        self.matcher = PersonaMatcher()
        self.prioritizer = PersonaPrioritizer()
    
    def assign_persona(
        self,
        user_id: str,
        window_type: str = '30d'
    ) -> Dict[str, any]:
        """Assign primary persona to a user.
        
        Args:
            user_id: User identifier
            window_type: '30d' or '180d' (will use best available)
            
        Returns:
            Dictionary with assignment details:
            - persona_name: Display name of assigned persona
            - priority_level: Priority level (1-5)
            - signal_strength: Calculated signal strength
            - decision_trace: JSON string with assignment rationale
            - assigned_at: Timestamp
        """
        # Get signals with graceful degradation
        degradation_result = self.degradation.get_signals_with_degradation(user_id)
        availability = degradation_result['data_availability']
        
        # Handle new users (<7 days)
        if availability == 'new':
            # Assign "Welcome" persona (not in enum, handled specially)
            return {
                'persona_name': 'Welcome',
                'priority_level': 0,  # Special priority for new users
                'signal_strength': 0.0,
                'decision_trace': json.dumps({
                    'reason': 'new_user',
                    'data_availability': availability,
                    'message': 'User has less than 7 days of data'
                }),
                'assigned_at': datetime.now().isoformat()
            }
        
        # Get primary signals (uses best available window)
        signals = self.degradation.get_primary_signals(user_id)
        
        # Match all applicable personas
        matching_personas = self.matcher.match_personas(signals)
        
        # Select primary persona
        primary_persona, decision_trace = self.prioritizer.select_primary_persona(
            matching_personas,
            signals
        )
        
        # Calculate signal strength for selected persona
        signal_strength = self.prioritizer._calculate_signal_strength(
            primary_persona,
            signals
        )
        
        # Complete decision trace
        decision_trace.update({
            'data_availability': availability,
            'window_type': signals.get('window_type', window_type),
            'all_matched_personas': [p.display_name for p in matching_personas],
            'selected_persona': primary_persona.display_name,
            'signal_strength': signal_strength
        })
        
        result = {
            'persona_name': primary_persona.display_name,
            'priority_level': primary_persona.priority,
            'signal_strength': signal_strength,
            'decision_trace': json.dumps(decision_trace),
            'assigned_at': datetime.now().isoformat()
        }
        
        logger.info(
            f"Assigned persona '{primary_persona.display_name}' to user {user_id} "
            f"(priority {primary_persona.priority}, strength {signal_strength:.2f})"
        )
        
        return result
    
    def save_assignment(
        self,
        user_id: str,
        assignment: Dict[str, any]
    ):
        """Save persona assignment to database.
        
        Args:
            user_id: User identifier
            assignment: Assignment dictionary from assign_persona()
        """
        cursor = self.conn.cursor()
        
        assignment_id = f"{user_id}_{assignment['assigned_at']}"
        
        cursor.execute("""
            INSERT OR REPLACE INTO personas (
                assignment_id, user_id, persona_name, assigned_at,
                priority_level, signal_strength, decision_trace
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            assignment_id,
            user_id,
            assignment['persona_name'],
            assignment['assigned_at'],
            assignment['priority_level'],
            assignment['signal_strength'],
            assignment['decision_trace']
        ))
        
        self.conn.commit()
        logger.debug(f"Saved persona assignment for user {user_id}")
    
    def assign_and_save(self, user_id: str) -> Dict[str, any]:
        """Assign persona and save to database in one operation.
        
        Args:
            user_id: User identifier
            
        Returns:
            Assignment dictionary
        """
        assignment = self.assign_persona(user_id)
        self.save_assignment(user_id, assignment)
        return assignment
    
    def get_assignment(self, user_id: str) -> Optional[Dict[str, any]]:
        """Get current persona assignment for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Assignment dictionary or None if not found
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT persona_name, priority_level, signal_strength,
                   decision_trace, assigned_at
            FROM personas
            WHERE user_id = ?
            ORDER BY assigned_at DESC
            LIMIT 1
        """, (user_id,))
        
        result = cursor.fetchone()
        
        if result:
            return {
                'persona_name': result['persona_name'],
                'priority_level': result['priority_level'],
                'signal_strength': result['signal_strength'],
                'decision_trace': json.loads(result['decision_trace']),
                'assigned_at': result['assigned_at']
            }
        
        return None

