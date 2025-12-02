"""
Gherkin Generator - Converts test scenarios to Gherkin .feature files
"""
import logging
from typing import List,Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class GherkinGenerator:
    """Generates Gherkin .feature files from test scenarios"""
    
    def generate_feature_file(self, url: str, scenarios: List[Any]) -> str:
        """
        Generate complete Gherkin feature file content
        
        Args:
            url: Website URL being tested
            scenarios: List of TestScenario objects
            
        Returns:
            Gherkin feature file content as string
        """
        if not scenarios:
            logger.warning("No scenarios provided for Gherkin generation")
            return self._generate_empty_feature(url)
        
        # Group scenarios by type
        hover_scenarios = [s for s in scenarios if s.scenario_type == 'hover']
        popup_scenarios = [s for s in scenarios if s.scenario_type == 'popup']
        
        output_lines = []
        
        # Add file header comment
        output_lines.append(f"# Auto-generated BDD test scenarios")
        output_lines.append(f"# URL: {url}")
        output_lines.append(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output_lines.append("")
        
        # Generate popup scenarios first (usually more important)
        if popup_scenarios:
            output_lines.extend(self._generate_scenarios_block(popup_scenarios))
            output_lines.append("")
        else:
            # Explicitly state that no popups were detected for this URL
            output_lines.extend(self._generate_no_popup_scenario(url))
            output_lines.append("")
        
        # Generate hover scenarios
        if hover_scenarios:
            output_lines.extend(self._generate_scenarios_block(hover_scenarios))
        
        return '\n'.join(output_lines)
    
    def _generate_scenarios_block(self, scenarios: List[Any]) -> List[str]:
        """Generate Gherkin content for a group of scenarios"""
        lines = []
        
        for scenario in scenarios:
            # Feature line
            lines.append(f"Feature: {scenario.feature_name}")
            lines.append("")
            
            # Scenario line
            lines.append(f"  Scenario: {scenario.scenario_name}")
            lines.append("")
            
            # Steps
            for step in scenario.steps:
                # Ensure proper indentation
                if not step.startswith('  '):
                    step = f"    {step}"
                lines.append(step)
            
            lines.append("")
        
        return lines
    
    def _generate_empty_feature(self, url: str) -> str:
        """Generate empty feature file when no scenarios detected"""
        return f"""# No interactive elements detected for {url}
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Feature: No testable interactions found

  Scenario: Manual review required
    Given the user navigates to "{url}"
    Then the page should load successfully
    # Note: No hoverable elements or popups were detected automatically
    # Manual test case creation may be required
"""

    def _generate_no_popup_scenario(self, url: str) -> list[str]:
        """Generate a small Gherkin block stating that no popups were detected."""
        lines: list[str] = []
        lines.append("Feature: No popup interactions detected")
        lines.append("")
        lines.append("  Scenario: Confirm absence of popups")
        lines.append("")
        lines.append(f"    Given the user is on \"{url}\" page")
        lines.append("    Then no pop-up dialogs should appear during automatic exploration")
        return lines
    
    def save_to_file(self, content: str, output_path: Path) -> None:
        """Save Gherkin content to .feature file"""
        output_path.write_text(content, encoding='utf-8')
        logger.info(f"Gherkin file saved: {output_path}")
    
    def validate_gherkin_syntax(self, content: str) -> bool:
        """
        Basic validation of Gherkin syntax
        
        Returns:
            True if valid, False otherwise
        """
        required_keywords = ['Feature:', 'Scenario:', 'Given', 'When', 'Then']
        
        for keyword in required_keywords:
            if keyword not in content:
                logger.warning(f"Missing required Gherkin keyword: {keyword}")
                return False
        
        return True