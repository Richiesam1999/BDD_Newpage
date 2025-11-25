"""
Interaction Mapper - Maps and organizes detected interactions
"""
import logging
from typing import List, Dict, Any
from collections import defaultdict
from dataclasses import asdict

logger = logging.getLogger(__name__)


class InteractionMapper:
    """Maps and organizes interactions for test generation"""
    
    def __init__(self):
        self.interactions: List[Any] = []
        self.hover_interactions: List[Any] = []
        self.popup_interactions: List[Any] = []
    
    def add_interaction(self, interaction) -> None:
        """Add an interaction to the collection"""
        self.interactions.append(interaction)
        
        if interaction.action_type == 'hover':
            self.hover_interactions.append(interaction)
        elif interaction.popup_appeared:
            self.popup_interactions.append(interaction)
        
        logger.debug(f"Added {interaction.action_type} interaction")
    
    def get_all_interactions(self) -> List[Any]:
        """Get all interactions"""
        return self.interactions
    
    def get_hover_interactions(self) -> List[Any]:
        """Get only hover interactions"""
        return self.hover_interactions
    
    def get_popup_interactions(self) -> List[Any]:
        """Get only popup interactions"""
        return self.popup_interactions
    
    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert interactions to dictionary format for AI processing"""
        result = []
        
        for interaction in self.interactions:
            interaction_dict = {
                'action_type': interaction.action_type,
                'trigger_element': {
                    'description': interaction.trigger_element.get_description(),
                    'text': interaction.trigger_element.text,
                    'tag': interaction.trigger_element.tag,
                    'role': interaction.trigger_element.role
                },
                'revealed_elements': [
                    {'description': el.get_description(), 'text': el.text}
                    for el in interaction.revealed_elements
                ],
                'url_changed': interaction.url_after is not None,
                'url_before': interaction.url_before,
                'url_after': interaction.url_after,
                'popup_appeared': interaction.popup_appeared
            }
            
            if interaction.popup_info:
                interaction_dict['popup_info'] = interaction.popup_info
            
            result.append(interaction_dict)
        
        return result
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        return {
            'total_interactions': len(self.interactions),
            'hover_count': len(self.hover_interactions),
            'popup_count': len(self.popup_interactions),
            'url_changes': sum(1 for i in self.interactions if i.url_after),
        }