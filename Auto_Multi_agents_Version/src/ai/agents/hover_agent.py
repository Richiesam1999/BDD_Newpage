"""
Hover Agent - Specializes in generating hover interaction scenarios
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class HoverScenario:
    """Represents a hover scenario"""
    feature_name: str
    scenario_name: str
    steps: List[str]
    confidence: float
    metadata: Dict


class HoverAgent:
    """
    Specialized agent for hover interactions
    Generates natural language test scenarios for hover behaviors
    """
    
    def __init__(self, llm_client):
        self.llm = llm_client
        self.agent_name = "Hover_Agent"
    
    async def generate_scenarios(self, hover_items: List[Dict], url: str) -> List[HoverScenario]:
        """
        Generate hover test scenarios
        
        Args:
            hover_items: List of hover interactions
            url: Page URL
            
        Returns:
            List of HoverScenario objects
        """
        logger.info(f"[{self.agent_name}] Generating scenarios for {len(hover_items)} hover interactions...")
        
        scenarios = []
        
        for item in hover_items:
            try:
                scenario = await self._generate_single_scenario(item, url)
                if scenario:
                    scenarios.append(scenario)
                    logger.debug(f"[{self.agent_name}] ✓ Generated: {scenario.scenario_name}")
            except Exception as e:
                logger.warning(f"[{self.agent_name}] Failed to generate scenario: {str(e)}")
        
        logger.info(f"[{self.agent_name}] Generated {len(scenarios)} hover scenarios")
        return scenarios
    
    async def _generate_single_scenario(self, item: Dict, url: str) -> Optional[HoverScenario]:
        """Generate a single hover scenario using LLM"""
        
        # Check if we have clickable links (deterministic approach)
        visual_changes = item.get('visual_changes', {})
        clickable_links = visual_changes.get('clickable_links', [])
        
        if clickable_links:
            # Use deterministic navigation-style scenario
            return self._generate_navigation_scenario(item, url, clickable_links)
        
        # Otherwise, use LLM to generate scenario
        element_desc = item['element']['description']
        trigger_text = item['trigger_text'] or 'navigation element'
        revealed_count = item.get('revealed_elements', 0)
        
        prompt = f"""You are a QA expert generating a hover test scenario.

CONTEXT:
- URL: {url}
- Element: {element_desc}
- Trigger Text: "{trigger_text}"
- Revealed Elements: {revealed_count}

Generate a natural language test scenario describing:
1. How to hover over the element
2. What becomes visible
3. What actions can be taken

Return JSON format:
{{
  "feature_name": "Validate [element] hover functionality",
  "scenario_name": "Verify [specific behavior]",
  "steps": [
    "Given the user is on \\"{url}\\" page",
    "When the user hovers over the \\"{trigger_text}\\"",
    "Then [expected outcome]"
  ]
}}

Be specific and avoid generic phrases like "button element"."""

        try:
            response = await self.llm.generate_json(prompt)
            
            return HoverScenario(
                feature_name=response.get('feature_name', 'Validate hover functionality'),
                scenario_name=response.get('scenario_name', 'Verify hover interaction'),
                steps=response.get('steps', []),
                confidence=0.8,
                metadata=item
            )
        except Exception as e:
            logger.error(f"[{self.agent_name}] LLM generation failed: {str(e)}")
            return self._generate_fallback_scenario(item, url)
    
    def _generate_navigation_scenario(self, item: Dict, url: str, links: List[Dict]) -> HoverScenario:
        """Generate deterministic navigation scenario when links are known"""
        
        trigger_text = item['trigger_text'] or 'navigation menu'
        
        # Find best link to use
        primary_link = self._select_primary_link(links, trigger_text)
        
        if primary_link:
            link_text = primary_link['text']
            target_url = primary_link['target_url']
            
            steps = [
                f'Given the user is on the "{url}" page',
                f'When the user hovers over the navigation menu "{trigger_text}"',
                f'And clicks the link "{link_text}" from the dropdown',
                f'Then the page URL should change to "{target_url}"'
            ]
            
            return HoverScenario(
                feature_name='Validate navigation menu functionality',
                scenario_name=f'Verify navigation from menu to {link_text}',
                steps=steps,
                confidence=0.9,
                metadata=item
            )
        
        return self._generate_fallback_scenario(item, url)
    
    def _select_primary_link(self, links: List[Dict], menu_label: str) -> Optional[Dict]:
        """Select the best link from dropdown"""
        banned_texts = {'help', 'support', 'contact', 'faq'}
        menu_lower = menu_label.lower()
        
        for link in links:
            text = link.get('text', '').strip()
            href = link.get('target_url', '').strip()
            
            if not text or not href:
                continue
            
            text_lower = text.lower()
            
            # Skip self-links
            if text_lower == menu_lower:
                continue
            
            # Skip generic help links (unless menu is Help)
            if menu_lower != 'help' and text_lower in banned_texts:
                continue
            
            return link
        
        return None
    
    def _generate_fallback_scenario(self, item: Dict, url: str) -> HoverScenario:
        """Generate fallback scenario when LLM fails"""
        
        trigger_text = item['trigger_text'] or 'navigation element'
        element_tag = item['element']['tag']
        
        steps = [
            f'Given the user is on "{url}" page',
            f'When the user hovers over the "{trigger_text}" {element_tag}',
            f'Then a dropdown menu with additional options should appear'
        ]
        
        return HoverScenario(
            feature_name=f'Validate {trigger_text} hover functionality',
            scenario_name=f'Verify hover behavior on {trigger_text}',
            steps=steps,
            confidence=0.5,
            metadata=item
        )
