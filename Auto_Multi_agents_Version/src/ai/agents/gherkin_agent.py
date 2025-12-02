"""
Gherkin Agent - Converts scenarios to proper Gherkin format
"""
import logging
from typing import List, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GherkinScenario:
    """Final Gherkin-formatted scenario"""
    feature_name: str
    scenario_name: str
    steps: List[str]
    scenario_type: str
    url: str
    confidence: float = 1.0


class GherkinAgent:
    """
    Specialized agent for Gherkin formatting
    Ensures all scenarios follow proper Gherkin syntax
    """
    
    def __init__(self, llm_client):
        self.llm = llm_client
        self.agent_name = "Gherkin_Agent"
    
    async def format_scenarios(
        self, 
        hover_scenarios: List, 
        popup_scenarios: List,
        url: str
    ) -> List[GherkinScenario]:
        """
        Format all scenarios into proper Gherkin
        
        Args:
            hover_scenarios: List of hover scenarios
            popup_scenarios: List of popup scenarios
            url: Page URL
            
        Returns:
            List of GherkinScenario objects
        """
        logger.info(f"[{self.agent_name}] Formatting {len(hover_scenarios)} hover + {len(popup_scenarios)} popup scenarios...")
        
        formatted = []
        
        # Format hover scenarios
        for scenario in hover_scenarios:
            try:
                gherkin = self._format_single_scenario(scenario, 'hover', url)
                if gherkin:
                    formatted.append(gherkin)
            except Exception as e:
                logger.warning(f"[{self.agent_name}] Failed to format hover scenario: {str(e)}")
        
        # Format popup scenarios
        for scenario in popup_scenarios:
            try:
                gherkin = self._format_single_scenario(scenario, 'popup', url)
                if gherkin:
                    formatted.append(gherkin)
            except Exception as e:
                logger.warning(f"[{self.agent_name}] Failed to format popup scenario: {str(e)}")
        
        logger.info(f"[{self.agent_name}] Formatted {len(formatted)} scenarios")
        return formatted
    
    def _format_single_scenario(self, scenario, scenario_type: str, url: str) -> GherkinScenario:
        """Format a single scenario"""
        
        # Ensure steps follow Gherkin keywords
        formatted_steps = self._ensure_gherkin_keywords(scenario.steps)
        
        return GherkinScenario(
            feature_name=scenario.feature_name,
            scenario_name=scenario.scenario_name,
            steps=formatted_steps,
            scenario_type=scenario_type,
            url=url,
            confidence=scenario.confidence
        )
    
    def _ensure_gherkin_keywords(self, steps: List[str]) -> List[str]:
        """Ensure steps start with proper Gherkin keywords"""
        
        if not steps:
            return steps
        
        formatted = []
        keywords = ['Given', 'When', 'Then', 'And', 'But']
        
        for i, step in enumerate(steps):
            step = step.strip()
            
            # Check if step already starts with keyword
            has_keyword = any(step.startswith(kw) for kw in keywords)
            
            if has_keyword:
                formatted.append(step)
            else:
                # Add appropriate keyword based on position
                if i == 0:
                    formatted.append(f'Given {step}')
                elif i == 1:
                    formatted.append(f'When {step}')
                elif i == 2:
                    formatted.append(f'Then {step}')
                else:
                    formatted.append(f'And {step}')
        
        return formatted
