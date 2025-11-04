"""Persona prioritization and selection logic"""

from typing import List, Dict, Tuple
from enum import Enum

from .criteria import Persona
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class PersonaPrioritizer:
    """Prioritizes and selects primary persona from matches"""
    
    def __init__(self):
        """Initialize prioritizer"""
        pass
    
    def select_primary_persona(
        self,
        matching_personas: List[Persona],
        signals: Dict[str, any]
    ) -> Tuple[Persona, Dict[str, any]]:
        """Select primary persona from matching personas.
        
        Selection logic:
        1. Apply priority order (1 = highest urgency)
        2. If multiple at same priority, use signal strength
        3. If still tied, use defined order
        
        Args:
            matching_personas: List of matching personas
            signals: Aggregated signals dictionary
            
        Returns:
            Tuple of (selected_persona, decision_trace)
        """
        if not matching_personas:
            # Default to Credit Builder if no matches
            return Persona.CREDIT_BUILDER, {
                'reason': 'no_matches',
                'matched_personas': []
            }
        
        if len(matching_personas) == 1:
            return matching_personas[0], {
                'reason': 'single_match',
                'matched_personas': [p.display_name for p in matching_personas]
            }
        
        # Group by priority
        by_priority: Dict[int, List[Persona]] = {}
        for persona in matching_personas:
            priority = persona.priority
            if priority not in by_priority:
                by_priority[priority] = []
            by_priority[priority].append(persona)
        
        # Select highest priority (lowest number)
        highest_priority = min(by_priority.keys())
        candidates = by_priority[highest_priority]
        
        decision_trace = {
            'reason': 'priority_selection',
            'matched_personas': [p.display_name for p in matching_personas],
            'highest_priority': highest_priority,
            'candidates_at_priority': [p.display_name for p in candidates]
        }
        
        # If multiple at same priority, use signal strength
        if len(candidates) > 1:
            strengths = {}
            for persona in candidates:
                strength = self._calculate_signal_strength(persona, signals)
                strengths[persona] = strength
            
            # Sort by strength (descending)
            sorted_candidates = sorted(
                candidates,
                key=lambda p: strengths[p],
                reverse=True
            )
            
            # If tied, use defined order
            max_strength = strengths[sorted_candidates[0]]
            tied_candidates = [
                p for p in sorted_candidates
                if strengths[p] == max_strength
            ]
            
            if len(tied_candidates) > 1:
                # Use defined order: High Util → Var Income → Credit → Sub → Savings
                defined_order = [
                    Persona.HIGH_UTILIZATION,
                    Persona.VARIABLE_INCOME,
                    Persona.CREDIT_BUILDER,
                    Persona.SUBSCRIPTION_HEAVY,
                    Persona.SAVINGS_BUILDER
                ]
                
                # Find first in defined order
                selected = None
                for persona in defined_order:
                    if persona in tied_candidates:
                        selected = persona
                        break
                
                decision_trace.update({
                    'tie_breaker': 'defined_order',
                    'signal_strengths': {
                        p.display_name: strengths[p] for p in candidates
                    },
                    'selected': selected.display_name if selected else None
                })
                
                return selected or tied_candidates[0], decision_trace
            else:
                decision_trace.update({
                    'tie_breaker': 'signal_strength',
                    'signal_strengths': {
                        p.display_name: strengths[p] for p in candidates
                    },
                    'selected': sorted_candidates[0].display_name
                })
                
                return sorted_candidates[0], decision_trace
        else:
            # Single candidate at highest priority
            decision_trace['selected'] = candidates[0].display_name
            return candidates[0], decision_trace
    
    def _calculate_signal_strength(self, persona: Persona, signals: Dict[str, any]) -> float:
        """Calculate signal strength for a persona.
        
        Args:
            persona: Persona to calculate strength for
            signals: Aggregated signals dictionary
            
        Returns:
            Signal strength value (sum of normalized signals)
        """
        subscriptions = signals.get('subscriptions', {})
        savings = signals.get('savings', {})
        credit = signals.get('credit', {})
        income = signals.get('income', {})
        
        # Normalize different signal types to 0-1 scale
        def normalize(value: float, min_val: float, max_val: float) -> float:
            if max_val == min_val:
                return 0.0
            return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))
        
        strength = 0.0
        
        if persona == Persona.HIGH_UTILIZATION:
            strength = (
                normalize(credit.get('credit_utilization', 0.0), 0, 100) +
                normalize(credit.get('interest_charges', 0.0), 0, 500) +
                (1.0 if credit.get('is_overdue', False) else 0.0)
            )
        
        elif persona == Persona.VARIABLE_INCOME:
            strength = (
                normalize(income.get('median_pay_gap_days', 0), 0, 90) +
                (1.0 - normalize(income.get('cash_flow_buffer_months', 0.0), 0, 3))
            )
        
        elif persona == Persona.CREDIT_BUILDER:
            # Lower credit usage = higher strength
            strength = (
                1.0 - normalize(credit.get('credit_utilization', 0.0), 0, 100)
            )
        
        elif persona == Persona.SUBSCRIPTION_HEAVY:
            strength = (
                normalize(subscriptions.get('subscriptions_count', 0), 0, 10) +
                normalize(subscriptions.get('monthly_recurring_spend', 0.0), 0, 500) +
                normalize(subscriptions.get('recurring_spend_share', 0.0), 0, 50)
            )
        
        elif persona == Persona.SAVINGS_BUILDER:
            strength = (
                normalize(savings.get('savings_growth_rate', 0.0), -10, 20) +
                normalize(savings.get('net_savings_inflow', 0.0), 0, 1000) +
                (1.0 - normalize(credit.get('credit_utilization', 0.0), 0, 30))
            )
        
        return strength

