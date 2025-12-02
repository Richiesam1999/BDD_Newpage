"""
Interaction Classifier Agent - Separates interactions by type
"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class InteractionClassifierAgent:
    """
    Classifies and separates interactions into specialized categories
    """
    
    def __init__(self):
        self.agent_name = "Interaction_Classifier_Agent"
    
    def classify(self, interactions: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Classify interactions into categories
        
        Args:
            interactions: List of classified interactions from DOM agent
            
        Returns:
            Dictionary with categorized interactions
        """
        logger.info(f"[{self.agent_name}] Classifying {len(interactions)} interactions...")
        
        categorized = {
            'hover': [],
            'popup': [],
            'click': [],
            'other': []
        }
        
        for interaction in interactions:
            interaction_type = interaction.get('type', 'other')
            
            if interaction_type in categorized:
                categorized[interaction_type].append(interaction)
            else:
                categorized['other'].append(interaction)
        
        # Log statistics
        logger.info(f"[{self.agent_name}] Classification results:")
        logger.info(f"  - Hover: {len(categorized['hover'])}")
        logger.info(f"  - Popup: {len(categorized['popup'])}")
        logger.info(f"  - Click: {len(categorized['click'])}")
        logger.info(f"  - Other: {len(categorized['other'])}")
        
        return categorized
