
#improved Vs
import logging
import json
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from urllib.parse import urlparse
from .llm_client import OllamaClient

logger = logging.getLogger(__name__)


@dataclass
class TestScenario:
    """Represents a generated test scenario"""
    feature_name: str
    scenario_name: str
    steps: List[str]
    scenario_type: str  # 'hover', 'popup', 'navigation'
    url: str
    confidence: float = 1.0
    
    def is_valid(self) -> bool:
        """Check if scenario is valid and meaningful"""
        # Must have steps
        if not self.steps or len(self.steps) < 3:
            return False
        
        # Steps must have actual content (not empty strings)
        if any(not step.strip() for step in self.steps):
            return False
        
        # Must have meaningful descriptions (not generic)
        generic_phrases = ["button element", "element", "the ''", "with the title ''"]
        scenario_text = " ".join(self.steps).lower()
        
        # Check for too many generic phrases
        generic_count = sum(1 for phrase in generic_phrases if phrase in scenario_text)
        if generic_count > 2:
            return False
        
        return True


class AgentOrchestrator:
    """
    Orchestrates multiple AI agents to generate test scenarios
    IMPROVED with quality controls and deduplication
    """
    
    def __init__(self, ollama_url: str = None, model: str = None):
        self.llm = OllamaClient(ollama_url, model)
        self._seen_scenarios: Set[str] = set()  # For deduplication
    
    async def generate_scenarios(
        self, 
        url: str, 
        interactions: List[Any],
        dom_structure: Dict[str, Any]
    ) -> List[TestScenario]:
        """
        Main orchestration method - generates test scenarios from interactions
        WITH QUALITY CONTROLS
        """
        logger.info("Starting AI agent workflow for scenario generation...")
        
        scenarios = []
        
        # Group interactions to avoid duplicates
        interaction_groups = self._group_interactions(interactions)
        
        # Process hover interactions
        for interaction in interaction_groups['hover']:
            try:
                scenario = await self._generate_hover_scenario(url, interaction, dom_structure)
                if scenario and scenario.is_valid() and self._is_unique_scenario(scenario):
                    scenarios.append(scenario)
                    logger.info(f"✓ Generated hover scenario: {scenario.scenario_name}")
                else:
                    logger.debug(f"✗ Rejected low-quality hover scenario")
            except Exception as e:
                logger.warning(f"Failed to generate hover scenario: {str(e)}")
        
        # Process popup interactions
        for interaction in interaction_groups['popup']:
            try:
                scenario = await self._generate_popup_scenario(url, interaction, dom_structure)
                if scenario and scenario.is_valid() and self._is_unique_scenario(scenario):
                    scenarios.append(scenario)
                    logger.info(f"✓ Generated popup scenario: {scenario.scenario_name}")
                else:
                    logger.debug(f"✗ Rejected low-quality popup scenario")
            except Exception as e:
                logger.warning(f"Failed to generate popup scenario: {str(e)}")
        
        logger.info(f"Generated {len(scenarios)} unique, quality scenarios")
        return scenarios
    
    def _group_interactions(self, interactions: List[Any]) -> Dict[str, List[Any]]:
        """Group and deduplicate interactions"""
        grouped = {'hover': [], 'popup': []}
        seen_elements = set()
        
        for interaction in interactions:
            # Create unique key for element
            element_key = (
                interaction.trigger_element.text[:50],
                interaction.trigger_element.tag,
                interaction.action_type
            )
            
            # Skip duplicates
            if element_key in seen_elements:
                continue
            
            seen_elements.add(element_key)
            
            if interaction.action_type == 'hover':
                grouped['hover'].append(interaction)
            elif interaction.popup_appeared:
                grouped['popup'].append(interaction)
        
        logger.info(f"Grouped: {len(grouped['hover'])} hover, {len(grouped['popup'])} popup (deduplicated)")
        return grouped
    
    def _is_unique_scenario(self, scenario: TestScenario) -> bool:
        """Check if scenario is unique"""
        # Create signature from steps
        signature = "|".join(scenario.steps)
        
        if signature in self._seen_scenarios:
            return False
        
        self._seen_scenarios.add(signature)
        return True
    
    async def _generate_hover_scenario(
        self, 
        url: str, 
        interaction: Any,
        dom_structure: Dict[str, Any]
    ) -> Optional[TestScenario]:
        """Generate test scenario for hover interaction.

        If we have concrete dropdown links (captured by ElementDetector as
        visual_changes["clickable_links"]), we prefer a deterministic
        navigation-style scenario (hover + click link + URL change) instead of
        asking the LLM to invent expected behavior. This produces outputs like
        the Tivdak examples you described.
        """
        # If dropdown links are known, use the deterministic fallback builder
        # which creates "from X page to Y page" navigation scenarios.
        visual_changes = getattr(interaction, "visual_changes", None)
        if isinstance(visual_changes, dict) and visual_changes.get("clickable_links"):
            return self._fallback_hover_scenario(url, interaction)
        
        context = self._prepare_hover_context(url, interaction, dom_structure)
        
        # Enhanced prompt with strict requirements
        prompt = f"""You are a QA automation expert generating Gherkin test scenarios.

CONTEXT:
- URL: {context['url']}
- Page Type: {context['page_type']}
- Element: {context['trigger_description']}
- What Appears on Hover: {context['revealed_description']}
- URL Changed: {context['url_changed']}

STRICT REQUIREMENTS:
1. Use SPECIFIC element descriptions (e.g., "New & Featured menu button", not "button element")
2. Describe ACTUAL behavior observed (what really appears on hover)
3. If it's a dropdown menu, say "dropdown menu" not "popup"
4. NO generic phrases like "button element", "the element", "additional content"
5. Steps must be clear, specific, and actionable
6. If you don't know what appears, describe it as "navigation options" or "dropdown items"

OUTPUT FORMAT (JSON only, no markdown):
{{
  "feature_name": "Validate [specific element] hover functionality",
  "scenario_name": "Verify [specific behavior] when hovering over [element]",
  "steps": [
    "Given the user is on \\"{context['url']}\\" page",
    "When the user hovers over the [SPECIFIC description]",
    "Then [SPECIFIC expected result]"
  ]
}}

EXAMPLE for Nike "New & Featured" button:
{{
  "feature_name": "Validate New & Featured menu navigation",
  "scenario_name": "Verify dropdown menu appears when hovering over New & Featured",
  "steps": [
    "Given the user is on \\"{context['url']}\\" page",
    "When the user hovers over the \\"New & Featured\\" navigation button",
    "Then a dropdown menu should appear with product categories",
    "And the menu should contain options like \\"Featured\\", \\"New Releases\\", and \\"Upcoming\\""
  ]
}}

Now generate for the provided context. Return ONLY valid JSON:"""

        try:
            response = await self.llm.generate_json(prompt)
            
            scenario = TestScenario(
                feature_name=response.get('feature_name', 'Validate hover functionality'),
                scenario_name=response.get('scenario_name', 'Verify hover interaction'),
                steps=response.get('steps', []),
                scenario_type='hover',
                url=url,
                confidence=0.8
            )
            
            # Validate quality
            if not scenario.is_valid():
                logger.warning("AI generated low-quality hover scenario, using fallback")
                return self._fallback_hover_scenario(url, interaction)
            
            return scenario
            
        except Exception as e:
            logger.error(f"AI generation failed for hover scenario: {str(e)}")
            return self._fallback_hover_scenario(url, interaction)
    
    async def _generate_popup_scenario(
        self,
        url: str,
        interaction: Any,
        dom_structure: Dict[str, Any]
    ) -> Optional[TestScenario]:
        """Generate test scenario for popup interaction using AI - IMPROVED"""
        
        context = self._prepare_popup_context(url, interaction, dom_structure)
        
        # Check if it's actually a popup or just a menu
        if not context['popup_title'] and not context['popup_buttons']:
            logger.debug("Not a true popup, skipping scenario generation")
            return None
        
        # Enhanced prompt with validation
        prompt = f"""You are a QA automation expert. Generate a Gherkin test scenario for this interaction.

CONTEXT:
- URL: {context['url']}
- Trigger Element: {context['trigger_description']}
- Popup/Modal Title: "{context['popup_title']}"
- Available Buttons: {context['popup_buttons']}
- URL Changes After: {context['url_changed']}

CRITICAL REQUIREMENTS:
1. Use the EXACT element description (don't say "button element" if you know it's "New & Featured")
2. Include the ACTUAL popup title in quotes (if title is empty, say "a modal dialog" or "an overlay")
3. Test ONLY the buttons that actually exist
4. If this is a dropdown menu (not a popup), describe it as "dropdown menu"
5. Be SPECIFIC about expected outcomes

DECISION TREE:
- If popup_title is empty AND no real buttons → This might be a dropdown menu, not a popup
- If popup has "OK" and "Cancel" → Test both actions
- If popup has "Continue" and "Cancel" → Test both actions  
- If popup has only one button → Test that one action

OUTPUT (JSON only):
{{
  "feature_name": "Validate [specific] functionality",
  "scenario_name": "Verify [specific behavior]",
  "steps": [
    "Given the user is on \\"{context['url']}\\" page",
    "When the user clicks the \\"[SPECIFIC element name]\\" button",
    "Then a [popup/modal/dropdown] should appear",
    "[Test specific button actions with actual button names]"
  ]
}}

GOOD EXAMPLE:
{{
  "feature_name": "Validate New & Featured menu functionality", 
  "scenario_name": "Verify dropdown navigation from New & Featured menu",
  "steps": [
    "Given the user is on \\"{context['url']}\\" page",
    "When the user clicks the \\"New & Featured\\" navigation button",
    "Then a dropdown menu should appear with product categories",
    "When the user clicks the \\"Featured\\" option from the menu",
    "Then the page should navigate to the featured products section"
  ]
}}

BAD EXAMPLE (don't do this):
{{
  "steps": [
    "When the user clicks the button element",
    "Then a popup should appear with the title ''",
    "When the user clicks the OK button"
  ]
}}

Generate for provided context:"""

        try:
            response = await self.llm.generate_json(prompt)
            
            scenario = TestScenario(
                feature_name=response.get('feature_name', 'Validate interaction'),
                scenario_name=response.get('scenario_name', 'Verify interaction'),
                steps=response.get('steps', []),
                scenario_type='popup',
                url=url,
                confidence=0.8
            )
            
            # Strict validation
            if not scenario.is_valid():
                logger.warning("AI generated low-quality popup scenario, using fallback")
                return self._fallback_popup_scenario(url, interaction)
            
            return scenario
            
        except Exception as e:
            logger.error(f"AI generation failed for popup scenario: {str(e)}")
            return self._fallback_popup_scenario(url, interaction)
    
    def _prepare_hover_context(self, url: str, interaction: Any, dom_structure: Dict) -> Dict[str, str]:
        """Prepare context for hover scenario generation"""
        # Get meaningful description of revealed elements
        if interaction.revealed_elements:
            revealed_texts = [el.text[:50] for el in interaction.revealed_elements[:3] if el.text]
            revealed_desc = ", ".join(revealed_texts) if revealed_texts else "navigation options or dropdown items"
        else:
            revealed_desc = "additional navigation options"
        
        return {
            'url': url,
            'page_type': dom_structure.get('page_type', 'general'),
            'trigger_description': interaction.trigger_element.get_description(),
            'revealed_description': revealed_desc,
            'url_changed': 'Yes' if interaction.url_after else 'No'
        }
    
    def _prepare_popup_context(self, url: str, interaction: Any, dom_structure: Dict) -> Dict[str, str]:
        """Prepare context for popup scenario generation"""
        popup_info = interaction.popup_info or {}
        
        # Get actual button names
        buttons = popup_info.get('buttons', [])
        button_names = [btn.get('text', '').strip() for btn in buttons if btn.get('text', '').strip()]
        buttons_str = ', '.join(button_names) if button_names else 'No buttons detected'
        
        return {
            'url': url,
            'page_type': dom_structure.get('page_type', 'general'),
            'trigger_description': interaction.trigger_element.get_description(),
            'popup_title': popup_info.get('title', '').strip(),
            'popup_buttons': buttons_str,
            'url_changed': 'Yes' if interaction.url_after else 'No'
        }
    
    def _fallback_hover_scenario(self, url: str, interaction: Any) -> TestScenario:
        """IMPROVED fallback template-based scenario.

        If we detected specific clickable links in the revealed dropdown, we
        generate a *navigation* style scenario like:

        Feature: Validate navigation menu functionality
        Scenario: Verify navigation from "Patient Stories" to "What is Tivdak" page
          Given the user is on the "https://.../patient-stories/" page
          When the user hovers over the navigation menu "About Tivdak"
          And clicks the link "What is Tivdak?" from the dropdown
          Then the page URL should change to "https://.../about-tivdak/"

        If we don't have link information, we fall back to the simpler "hover
        shows additional content" variant.
        """
        trigger_text = (interaction.trigger_element.text or "").strip()[:50]
        element_tag = interaction.trigger_element.tag or "element"

        # Try to get clickable links captured by the ElementDetector
        clickable_links = []
        visual_changes = getattr(interaction, "visual_changes", None)
        if isinstance(visual_changes, dict):
            clickable_links = visual_changes.get("clickable_links") or []

        # Helper: derive a human label for the current page from the URL
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        if path:
            last_segment = path.split("/")[-1]
            from_label = last_segment.replace("-", " ").replace("_", " ").title()
        else:
            # Home page – use domain as label
            from_label = parsed.netloc

        # If we have at least one meaningful link in the dropdown, generate
        # a navigation scenario that clicks that link.
        #
        # Heuristics to avoid obviously wrong/global links:
        # - Skip links whose text equals the menu label (top-level trigger)
        # - For non-"Help" menus, skip generic help/support links
        # - Require target URL to differ from the current page URL
        banned_help_texts = {
            "help",
            "customer service",
            "support",
            "contact us",
            "contact",
            "faq",
        }

        primary_link = None
        menu_label_lower = (trigger_text or "").strip().lower()

        for link in clickable_links:
            text = (link.get("text") or "").strip()
            href = (link.get("target_url") or "").strip()
            if not text or not href:
                continue

            text_lower = text.lower()

            # Skip self-links (same label as the menu trigger)
            if menu_label_lower and text_lower == menu_label_lower:
                continue

            # For menus other than "Help", avoid global help-style links
            if menu_label_lower != "help" and text_lower in banned_help_texts:
                continue

            # Require that the link actually navigates away from the current page
            if href.rstrip("/") == url.rstrip("/"):
                continue

            primary_link = {"text": text, "href": href}
            break

        if primary_link:
            link_text = primary_link["text"]
            target_url = primary_link["href"]

            # Build a reasonable "to" label from the link text
            to_label = link_text.strip().strip("?")

            feature_name = "Validate navigation menu functionality"
            scenario_name = (
                f'Verify navigation from "{from_label}" to "{to_label}" page'
            )

            menu_label = trigger_text or element_tag

            steps = [
                f'Given the user is on the "{url}" page',
                f'When the user hovers over the navigation menu "{menu_label}"',
                f'And clicks the link "{link_text}" from the dropdown',
                f'Then the page URL should change to "{target_url}"',
            ]

            return TestScenario(
                feature_name=feature_name,
                scenario_name=scenario_name,
                steps=steps,
                scenario_type='hover',
                url=url,
                confidence=0.7,
            )

        # ---- Fallback when we don't have link information ----
        element_text = trigger_text or "navigation element"

        if element_text:
            element_desc = f'"{element_text}" {element_tag}'
        else:
            element_desc = f'{element_tag} element in navigation'

        revealed = interaction.revealed_elements
        if revealed and any(el.text for el in revealed):
            outcome = "a dropdown menu with additional options should appear"
        else:
            outcome = "additional navigation content should become visible"

        steps = [
            f'Given the user is on "{url}" page',
            f'When the user hovers over the {element_desc}',
            f'Then {outcome}',
        ]

        if interaction.url_after:
            steps.append(f'And the page URL should change to "{interaction.url_after}"')

        return TestScenario(
            feature_name=f'Validate hover interaction on {element_text or element_tag}',
            scenario_name=f'Verify hover behavior on {element_desc}',
            steps=steps,
            scenario_type='hover',
            url=url,
            confidence=0.5,
        )
    
    def _fallback_popup_scenario(self, url: str, interaction: Any) -> TestScenario:
        """IMPROVED fallback template-based scenario for popups.

        When multiple buttons exist (e.g., "Cancel" and "Continue"), we
        generate a scenario that tests BOTH flows:
        - Clicking the cancel/close button keeps the user on the same page.
        - Clicking the continue/primary button navigates to the appropriate URL
          (using the button href if available, otherwise interaction.url_after).
        """
        element_text = interaction.trigger_element.text[:50] if interaction.trigger_element.text else None
        popup_info = interaction.popup_info or {}
        
        # Build meaningful element description
        if element_text:
            element_desc = f'"{element_text}" button'
        else:
            element_desc = 'navigation button'
        
        popup_title = popup_info.get('title', '').strip()
        buttons = popup_info.get('buttons', [])

        # Classify buttons into cancel/close vs primary/continue
        go_words = ["continue", "yes", "ok", "proceed", "accept", "confirm"]
        cancel_words = ["cancel", "close", "no", "stay", "dismiss"]

        def classify_button(btn: Dict[str, Any]) -> str:
            text = (btn.get('text') or '').strip().lower()
            if any(w in text for w in cancel_words):
                return 'cancel'
            if any(w in text for w in go_words):
                return 'go'
            return 'other'

        go_button = None
        cancel_button = None
        other_buttons: List[Dict[str, Any]] = []
        for btn in buttons:
            kind = classify_button(btn)
            if kind == 'cancel' and not cancel_button:
                cancel_button = btn
            elif kind == 'go' and not go_button:
                go_button = btn
            else:
                other_buttons.append(btn)

        # Fallbacks if classification failed
        if not go_button and buttons:
            go_button = buttons[0]
        if not cancel_button and len(buttons) > 1:
            cancel_button = buttons[1]
        
        steps: List[str] = []

        # Base: open popup
        steps.append(f'Given the user is on "{url}" page')
        steps.append(f'When the user clicks the {element_desc}')
        if popup_title:
            steps.append(f'Then a modal dialog should appear with the title "{popup_title}"')
        else:
            steps.append('Then a dropdown menu or overlay should appear')

        # If we have both cancel and go buttons, generate two flows
        def btn_text(btn: Optional[Dict[str, Any]]) -> Optional[str]:
            return (btn or {}).get('text', '').strip() or None

        def btn_href(btn: Optional[Dict[str, Any]]) -> Optional[str]:
            return (btn or {}).get('href', '').strip() or None

        cancel_text = btn_text(cancel_button)
        go_text = btn_text(go_button)
        go_href = btn_href(go_button)

        if cancel_text and go_text and cancel_text != go_text:
            # Cancel/close branch
            steps.append(f'When the user clicks the "{cancel_text}" button')
            steps.append('Then the dialog should close')
            steps.append('And the user should remain on the same page')

            # Re-open for continue branch
            steps.append(f'When the user clicks the {element_desc} again')
            if popup_title:
                steps.append(f'Then a modal dialog should appear with the title "{popup_title}"')
            else:
                steps.append('Then a dropdown menu or overlay should appear')

            # Continue/primary branch
            steps.append(f'When the user clicks the "{go_text}" button')
            target_url = go_href or (interaction.url_after or '').strip()
            if target_url:
                steps.append(f'Then the page should navigate to "{target_url}"')
            else:
                steps.append('Then the dialog should close')
        else:
            # Single-button or unclassified case: fall back to simpler behavior
            if go_text:
                steps.append(f'When the user clicks the "{go_text}" button')
                target_url = go_href or (interaction.url_after or '').strip()
                if target_url:
                    steps.append(f'Then the page should navigate to "{target_url}"')
                else:
                    steps.append('Then the dialog should close')
            else:
                # No clear buttons: just assert the popup appears
                steps.append('And the user can close the dialog')
        
        return TestScenario(
            feature_name=f'Validate {element_text or "navigation"} interaction',
            scenario_name=f'Verify behavior when clicking {element_desc}',
            steps=steps,
            scenario_type='popup',
            url=url,
            confidence=0.5
        )
