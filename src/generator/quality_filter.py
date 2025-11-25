"""
Quality Filter - Post-processing to ensure high-quality scenarios
"""
import logging
from typing import List,Any
import re

logger = logging.getLogger(__name__)


class QualityFilter:
    """Filters and improves test scenarios before output"""
    
    # Patterns that indicate low quality
    LOW_QUALITY_PATTERNS = [
        r"button element",
        r"the element",
        r"a element",
        r"with the title ''",
        r"with the title \"\"",
        r"should appear with ''",
        r"clicks the  button",  # double space
        r"clicks the \"\" button",  # empty button name
        r"the popup should appear with the title ",
    ]
    
    # Generic phrases to replace with better alternatives
    IMPROVEMENTS = {
        r"additional content should appear": "a dropdown menu or overlay should appear",
        r"button element": "navigation button",
        r"the element": "the navigation element",
        r"with the title ''": "with a title",
        r'with the title ""': "with a title",
    }
    
    @staticmethod
    def filter_scenarios(scenarios: List[Any]) -> List[Any]:
        """
        Filter out low-quality scenarios and improve remaining ones
        
        Args:
            scenarios: List of TestScenario objects
            
        Returns:
            Filtered list of high-quality scenarios
        """
        filtered = []
        
        for scenario in scenarios:
            # Check if scenario meets quality standards
            if QualityFilter._is_quality_scenario(scenario):
                # Improve the scenario
                improved = QualityFilter._improve_scenario(scenario)
                filtered.append(improved)
                logger.info(f"✓ Accepted: {scenario.scenario_name}")
            else:
                logger.warning(f"✗ Rejected low-quality: {scenario.scenario_name}")
        
        logger.info(f"Quality filter: {len(filtered)}/{len(scenarios)} scenarios passed")
        return filtered
    
    @staticmethod
    def _is_quality_scenario(scenario: Any) -> bool:
        """Check if scenario meets quality standards"""
        
        # Must have at least 3 steps
        if not scenario.steps or len(scenario.steps) < 3:
            return False
        
        # Check for low-quality patterns
        all_text = " ".join(scenario.steps + [scenario.scenario_name, scenario.feature_name])
        
        low_quality_count = 0
        for pattern in QualityFilter.LOW_QUALITY_PATTERNS:
            if re.search(pattern, all_text, re.IGNORECASE):
                low_quality_count += 1
        
        # Reject if too many low-quality indicators
        if low_quality_count > 2:
            return False
        
        # Must have meaningful Given/When/Then
        has_given = any("Given" in step for step in scenario.steps)
        has_when = any("When" in step for step in scenario.steps)
        has_then = any("Then" in step for step in scenario.steps)
        
        if not (has_given and has_when and has_then):
            return False
        
        # Check for empty strings or meaningless content
        if any(step.strip() in ["", "Given", "When", "Then", "And"] for step in scenario.steps):
            return False
        
        return True
    
    @staticmethod
    def _improve_scenario(scenario: Any) -> Any:
        """Improve scenario by replacing generic phrases"""
        
        # Improve steps
        improved_steps = []
        for step in scenario.steps:
            improved_step = step
            
            # Apply improvements
            for pattern, replacement in QualityFilter.IMPROVEMENTS.items():
                improved_step = re.sub(pattern, replacement, improved_step, flags=re.IGNORECASE)
            
            # Clean up extra spaces
            improved_step = re.sub(r'\s+', ' ', improved_step).strip()
            
            improved_steps.append(improved_step)
        
        # Update scenario
        scenario.steps = improved_steps
        
        # Improve feature name
        for pattern, replacement in QualityFilter.IMPROVEMENTS.items():
            scenario.feature_name = re.sub(pattern, replacement, scenario.feature_name, flags=re.IGNORECASE)
        
        # Improve scenario name
        for pattern, replacement in QualityFilter.IMPROVEMENTS.items():
            scenario.scenario_name = re.sub(pattern, replacement, scenario.scenario_name, flags=re.IGNORECASE)
        
        return scenario
    
    @staticmethod
    def deduplicate_scenarios(scenarios: List[Any]) -> List[Any]:
        """Remove duplicate scenarios based on step similarity.

        Special handling for navigation-from-dropdown scenarios so that flows
        like "click Help from dropdown to go to /help" are kept only once,
        even if generated for multiple top-level menus.
        """
        unique_scenarios = []
        seen_signatures = set()
        
        for scenario in scenarios:
            # Create signature from steps (ignoring Given step which is often identical)
            action_steps = [s.strip() for s in scenario.steps if not s.strip().startswith("Given")]

            # Special case 1: navigation-from-dropdown pattern
            nav_target = None
            nav_link = None
            for step in action_steps:
                m_url = re.search(r'Then the page URL should change to "([^"]+)"', step)
                if m_url:
                    nav_target = m_url.group(1)
                m_link = re.search(r'clicks the link "([^"]+)" from the dropdown', step, re.IGNORECASE)
                if m_link:
                    nav_link = m_link.group(1)

            if nav_target and nav_link:
                # Use a normalized signature so identical flows dedupe even if
                # the hovered menu text differs.
                signature = f"NAV|{nav_link}|{nav_target}"
            else:
                # Special case 2: popup scenarios for the same modal title
                sig_prefix = None
                scenario_type = getattr(scenario, "scenario_type", None)
                if scenario_type == "popup":
                    # Look for a quoted modal title like "Cookie Disclaimer" in any step
                    joined = " ".join(action_steps)
                    m_title = re.search(r'"([^"]*Cookie Disclaimer[^"]*)"', joined, re.IGNORECASE)
                    if m_title:
                        # All Cookie Disclaimer flows collapse to one logical popup
                        sig_prefix = f"POPUP|{m_title.group(1).strip().lower()}"

                if sig_prefix:
                    signature = sig_prefix
                else:
                    signature = "|".join(sorted(action_steps))
            
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_scenarios.append(scenario)
            else:
                logger.debug(f"Removed duplicate: {scenario.scenario_name}")
        
        logger.info(f"Deduplication: {len(unique_scenarios)}/{len(scenarios)} unique scenarios")
        return unique_scenarios
    
    @staticmethod
    def sort_by_importance(scenarios: List[Any]) -> List[Any]:
        """Sort scenarios by importance (popup first, then hover)"""
        popup_scenarios = [s for s in scenarios if s.scenario_type == 'popup']
        hover_scenarios = [s for s in scenarios if s.scenario_type == 'hover']
        
        return popup_scenarios + hover_scenarios
    
    @staticmethod
    def process_scenarios(scenarios: List[Any]) -> List[Any]:
        """
        Complete processing pipeline: filter, improve, deduplicate, sort
        
        Args:
            scenarios: Raw scenarios from AI
            
        Returns:
            High-quality, deduplicated, sorted scenarios
        """
        logger.info(f"Processing {len(scenarios)} raw scenarios...")
        
        # Step 1: Filter low quality
        filtered = QualityFilter.filter_scenarios(scenarios)
        
        # Step 2: Deduplicate
        unique = QualityFilter.deduplicate_scenarios(filtered)
        
        # Step 3: Sort by importance
        sorted_scenarios = QualityFilter.sort_by_importance(unique)
        
        logger.info(f"✓ Final output: {len(sorted_scenarios)} high-quality scenarios")
        return sorted_scenarios