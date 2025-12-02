"""
DOM Analysis Agent - Analyzes DOM structure and classifies elements
"""
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class DOMAnalysisAgent:
    """
    Analyzes DOM structure and classifies interactive elements
    """
    
    def __init__(self, llm_client):
        self.llm = llm_client
        self.agent_name = "DOM_Analysis_Agent"
    
    async def analyze(self, interactions: List[Any], dom_structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze interactions and classify them with metadata
        
        Args:
            interactions: Raw interactions from element detector
            dom_structure: Analyzed DOM structure
            
        Returns:
            List of classified interactions with metadata
        """
        logger.info(f"[{self.agent_name}] Analyzing {len(interactions)} interactions...")
        
        classified = []
        
        for interaction in interactions:
            try:
                # Extract element information
                element_info = self._extract_element_info(interaction)
                
                # Classify interaction type
                interaction_type = self._classify_interaction(interaction)
                
                # Build metadata
                metadata = {
                    'type': interaction_type,
                    'element': element_info,
                    'trigger_text': interaction.trigger_element.text[:100] if interaction.trigger_element.text else '',
                    'trigger_tag': interaction.trigger_element.tag,
                    'action_type': interaction.action_type,
                    'has_popup': interaction.popup_appeared if hasattr(interaction, 'popup_appeared') else False,
                    'url_changed': bool(interaction.url_after) if hasattr(interaction, 'url_after') else False,
                    'raw_interaction': interaction
                }
                
                # Add type-specific metadata
                if interaction_type == 'hover':
                    metadata['revealed_elements'] = len(interaction.revealed_elements) if hasattr(interaction, 'revealed_elements') else 0
                    metadata['visual_changes'] = getattr(interaction, 'visual_changes', {})
                elif interaction_type == 'popup':
                    metadata['popup_info'] = interaction.popup_info if hasattr(interaction, 'popup_info') else {}
                
                classified.append(metadata)
                
            except Exception as e:
                logger.warning(f"[{self.agent_name}] Failed to classify interaction: {str(e)}")
                continue
        
        logger.info(f"[{self.agent_name}] Classified {len(classified)} interactions")
        return classified
    
    def _extract_element_info(self, interaction: Any) -> Dict[str, str]:
        """Extract element information"""
        return {
            'text': interaction.trigger_element.text[:100] if interaction.trigger_element.text else '',
            'tag': interaction.trigger_element.tag or 'unknown',
            'description': interaction.trigger_element.get_description() if hasattr(interaction.trigger_element, 'get_description') else 'element'
        }
    
    def _classify_interaction(self, interaction: Any) -> str:
        """Classify interaction type"""
        if hasattr(interaction, 'popup_appeared') and interaction.popup_appeared:
            return 'popup'
        elif hasattr(interaction, 'action_type') and interaction.action_type == 'hover':
            return 'hover'
        elif hasattr(interaction, 'action_type') and interaction.action_type == 'click':
            return 'click'
        else:
            return 'other'
