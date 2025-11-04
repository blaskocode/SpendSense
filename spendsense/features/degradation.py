"""Graceful degradation for new users with limited data"""

from typing import Dict, Optional
from datetime import date

from .aggregator import SignalAggregator
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class GracefulDegradation:
    """Handles graceful degradation for users with limited data"""
    
    def __init__(self, aggregator: SignalAggregator):
        """Initialize graceful degradation handler.
        
        Args:
            aggregator: Signal aggregator instance
        """
        self.aggregator = aggregator
    
    def get_signals_with_degradation(
        self,
        user_id: str
    ) -> Dict[str, any]:
        """Get signals with appropriate degradation based on data availability.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with signals and degradation metadata:
            - signals: Computed signals (may be partial)
            - data_availability: Classification string
            - disclaimer: Optional disclaimer message
            - can_compute_30d: Whether 30-day window can be computed
            - can_compute_180d: Whether 180-day window can be computed
        """
        availability = self.aggregator.get_user_data_availability(user_id)
        
        result = {
            'data_availability': availability,
            'can_compute_30d': False,
            'can_compute_180d': False,
            'signals_30d': None,
            'signals_180d': None,
            'disclaimer': None
        }
        
        if availability == 'new':
            # <7 days: Welcome persona, basic education only
            result['disclaimer'] = (
                "Welcome! We're still learning about your financial patterns. "
                "As we gather more data, your insights will become more personalized."
            )
            logger.info(f"User {user_id}: New user (<7 days), using welcome persona")
            
        elif availability == 'limited':
            # 7-29 days: Preliminary insights with disclaimer
            result['can_compute_30d'] = True
            result['signals_30d'] = self.aggregator.compute_signals(user_id, '30d')
            result['disclaimer'] = (
                "We're building your financial profile. These are preliminary insights. "
                "After 30 days of data, you'll receive more detailed recommendations."
            )
            logger.info(f"User {user_id}: Limited data (7-29 days), preliminary insights")
            
        elif availability == 'full_30':
            # 30+ days: Full 30-day analysis
            result['can_compute_30d'] = True
            result['signals_30d'] = self.aggregator.compute_signals(user_id, '30d')
            logger.info(f"User {user_id}: Full 30-day analysis available")
            
        elif availability == 'full_180':
            # 180+ days: Both windows available
            result['can_compute_30d'] = True
            result['can_compute_180d'] = True
            result['signals_30d'] = self.aggregator.compute_signals(user_id, '30d')
            result['signals_180d'] = self.aggregator.compute_signals(user_id, '180d')
            logger.info(f"User {user_id}: Full analysis available (30d and 180d)")
        
        return result
    
    def get_primary_signals(self, user_id: str) -> Dict[str, any]:
        """Get primary signals for persona assignment (uses best available window).
        
        Args:
            user_id: User identifier
            
        Returns:
            Primary signals dictionary (from best available window)
        """
        degradation_result = self.get_signals_with_degradation(user_id)
        
        # Prefer 180d if available, otherwise 30d, otherwise None
        if degradation_result['signals_180d']:
            return degradation_result['signals_180d']
        elif degradation_result['signals_30d']:
            return degradation_result['signals_30d']
        else:
            # Return empty signals structure for new users
            return {
                'user_id': user_id,
                'window_type': 'new',
                'computed_at': None,
                'subscriptions': {'subscriptions_count': 0},
                'savings': {'savings_growth_rate': 0.0},
                'credit': {'credit_utilization': 0.0},
                'income': {'cash_flow_buffer_months': 0.0}
            }

