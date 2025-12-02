"""
Popup Agent - Specializes in generating popup/modal interaction scenarios
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PopupScenario:
    """Represents a popup scenario"""
    feature_name: str
    scenario_name: str
    steps: List[str]
    confidence: float
    metadata: Dict


class PopupAgent:
    """
    Specialized agent for popup/modal interactions
    Generates natural language test scenarios for popup behaviors
    """
    
    def __init__(self, llm_client):
        self.llm = llm_client
        self.agent_name = "Popup_Agent"
    
    async def generate_scenarios(self, popup_items: List[Dict], url: str) -> List[PopupScenario]:
        """
        Generate popup test scenarios
        
        Args:
            popup_items: List of popup interactions
            url: Page URL
            
        Returns:
            List of PopupScenario objects
        """
        logger.info(f"[{self.agent_name}] Generating scenarios for {len(popup_items)} popup interactions...")
        
        scenarios = []
        
        for item in popup_items:
            try:
                scenario = await self._generate_single_scenario(item, url)
                if scenario:
                    scenarios.append(scenario)
                    logger.debug(f"[{self.agent_name}] ✓ Generated: {scenario.scenario_name}")
            except Exception as e:
                logger.warning(f"[{self.agent_name}] Failed to generate scenario: {str(e)}")
        
        logger.info(f"[{self.agent_name}] Generated {len(scenarios)} popup scenarios")
        return scenarios
    
    async def _generate_single_scenario(self, item: Dict, url: str) -> Optional[PopupScenario]:
        """Generate a single popup scenario using LLM"""
        
        popup_info = item.get('popup_info', {})
        popup_title = popup_info.get('title', '').strip()
        buttons = popup_info.get('buttons', [])
        
        # Skip if not a real popup
        if not popup_title and not buttons:
            logger.debug(f"[{self.agent_name}] Skipping non-popup interaction")
            return None
        
        element_desc = item['element']['description']
        trigger_text = item['trigger_text'] or 'button'
        button_names = [btn.get('text', '').strip() for btn in buttons if btn.get('text', '').strip()]
        
        prompt = f"""You are a QA expert generating a popup test scenario.

CONTEXT:
- URL: {url}
- Trigger Element: {element_desc}
- Trigger Text: "{trigger_text}"
- Popup Title: "{popup_title}"
- Buttons: {', '.join(button_names) if button_names else 'None'}

Generate a comprehensive test scenario that tests ALL button actions.

REQUIREMENTS:
1. Test Cancel/Close button (if exists) - verify popup closes
2. Test Continue/Confirm button (if exists) - verify expected action
3. Use exact button names
4. Include popup title in quotes

Return JSON format:
{{
  "feature_name": "Validate [trigger] popup functionality",
  "scenario_name": "Verify popup behavior with [buttons]",
  "steps": [
    "Given the user is on \\"{url}\\" page",
    "When the user clicks the \\"{trigger_text}\\" button",
    "Then a popup should appear with the title \\"{popup_title}\\"",
    "When the user clicks the \\"[Button1]\\" button",
    "Then [expected outcome]",
    "When the user clicks the \\"{trigger_text}\\" button",
    "Then a popup should appear with the title \\"{popup_title}\\"",
    "When the user clicks the \\"[Button2]\\" button",
    "Then [expected outcome]"
  ]
}}

Test BOTH buttons in sequence."""

        try:
            response = await self.llm.generate_json(prompt)
            
            return PopupScenario(
                feature_name=response.get('feature_name', 'Validate popup functionality'),
                scenario_name=response.get('scenario_name', 'Verify popup interaction'),
                steps=response.get('steps', []),
                confidence=0.8,
                metadata=item
            )
        except Exception as e:
            logger.error(f"[{self.agent_name}] LLM generation failed: {str(e)}")
            return self._generate_fallback_scenario(item, url)
    
    def _generate_fallback_scenario(self, item: Dict, url: str) -> PopupScenario:
        """Generate fallback scenario when LLM fails"""
        
        trigger_text = item['trigger_text'] or 'button'
        popup_info = item.get('popup_info', {})
        popup_title = popup_info.get('title', '').strip()
        buttons = popup_info.get('buttons', [])
        
        steps = [
            f'Given the user is on "{url}" page',
            f'When the user clicks the "{trigger_text}" button'
        ]
        
        if popup_title:
            steps.append(f'Then a popup should appear with the title "{popup_title}"')
        else:
            steps.append('Then a modal dialog should appear')
        
        # Classify buttons
        go_button = None
        cancel_button = None
        
        for btn in buttons:
            text = btn.get('text', '').strip().lower()
            if any(w in text for w in ['cancel', 'close', 'no']):
                cancel_button = btn
            elif any(w in text for w in ['continue', 'yes', 'ok', 'confirm']):
                go_button = btn
        
        # Test both buttons if available
        if cancel_button:
            steps.append(f'When the user clicks the "{cancel_button.get("text")}" button')
            steps.append('Then the popup should close')
            steps.append('And the user should remain on the same page')
        
        if go_button:
            steps.append(f'When the user clicks the "{trigger_text}" button')
            if popup_title:
                steps.append(f'Then a popup should appear with the title "{popup_title}"')
            steps.append(f'When the user clicks the "{go_button.get("text")}" button')
            
            # Check if we have URL change info
            if item.get('url_changed'):
                steps.append('Then the page should navigate to the target URL')
            else:
                steps.append('Then the popup should close')
        
        return PopupScenario(
            feature_name=f'Validate {trigger_text} popup functionality',
            scenario_name=f'Verify popup behavior when clicking {trigger_text}',
            steps=steps,
            confidence=0.5,
            metadata=item
        )
