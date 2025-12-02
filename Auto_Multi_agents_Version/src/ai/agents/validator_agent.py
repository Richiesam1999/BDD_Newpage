"""
Validator Agent - Validates scenario quality and Gherkin correctness
"""
import logging
from typing import List
import re

logger = logging.getLogger(__name__)


class ValidatorAgent:
    """
    Validates scenarios for quality and correctness
    """
    
    def __init__(self):
        self.agent_name = "Validator_Agent"
    
    def validate_scenarios(self, scenarios: List) -> List:
        """
        Validate and filter scenarios
        
        Args:
            scenarios: List of GherkinScenario objects
            
        Returns:
            List of valid scenarios
        """
        logger.info(f"[{self.agent_name}] Validating {len(scenarios)} scenarios...")
        
        valid_scenarios = []
        
        for scenario in scenarios:
            issues = self._check_scenario(scenario)
            
            if not issues:
                valid_scenarios.append(scenario)
                logger.debug(f"[{self.agent_name}] ✓ Valid: {scenario.scenario_name}")
            else:
                logger.warning(f"[{self.agent_name}] ✗ Invalid: {scenario.scenario_name}")
                for issue in issues:
                    logger.warning(f"  - {issue}")
        
        logger.info(f"[{self.agent_name}] {len(valid_scenarios)}/{len(scenarios)} scenarios passed validation")
        return valid_scenarios
    
    def _check_scenario(self, scenario) -> List[str]:
        """Check a single scenario for issues"""
        
        issues = []
        
        # Check 1: Must have steps
        if not scenario.steps or len(scenario.steps) < 3:
            issues.append("Too few steps (minimum 3 required)")
        
        # Check 2: Steps must not be empty
        if any(not step.strip() for step in scenario.steps):
            issues.append("Contains empty steps")
        
        # Check 3: Steps must start with Gherkin keywords
        valid_keywords = ['Given', 'When', 'Then', 'And', 'But']
        for i, step in enumerate(scenario.steps):
            if not any(step.strip().startswith(kw) for kw in valid_keywords):
                issues.append(f"Step {i+1} missing Gherkin keyword: '{step[:50]}'")
        
        # Check 4: Must have Given, When, Then
        step_text = ' '.join(scenario.steps)
        if 'Given' not in step_text:
            issues.append("Missing 'Given' step")
        if 'When' not in step_text:
            issues.append("Missing 'When' step")
        if 'Then' not in step_text:
            issues.append("Missing 'Then' step")
        
        # Check 5: Avoid generic phrases
        generic_phrases = ["button element", "the ''", "with the title ''", "element element"]
        scenario_text = ' '.join(scenario.steps).lower()
        
        for phrase in generic_phrases:
            if phrase in scenario_text:
                issues.append(f"Contains generic phrase: '{phrase}'")
        
        # Check 6: Feature and scenario names must not be empty
        if not scenario.feature_name or not scenario.feature_name.strip():
            issues.append("Empty feature name")
        if not scenario.scenario_name or not scenario.scenario_name.strip():
            issues.append("Empty scenario name")
        
        # Check 7: Check for hallucinated selectors (CSS/XPath)
        selector_patterns = [
            r'#[a-zA-Z0-9_-]+',  # CSS ID
            r'\.[a-zA-Z0-9_-]+',  # CSS class (but allow URLs)
            r'//[a-zA-Z]+\[',  # XPath
        ]
        
        for pattern in selector_patterns:
            if re.search(pattern, scenario_text) and 'http' not in scenario_text:
                issues.append(f"Contains technical selector: {pattern}")
        
        return issues
