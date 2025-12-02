"""
Multi-Agent Orchestrator - Uses LangGraph workflow
This is the new orchestrator that replaces the single-agent approach
"""
import logging
from typing import List, Dict, Any
from dataclasses import dataclass

from .graph.workflow import MultiAgentWorkflow

logger = logging.getLogger(__name__)


@dataclass
class TestScenario:
    """Represents a generated test scenario (compatible with existing code)"""
    feature_name: str
    scenario_name: str
    steps: List[str]
    scenario_type: str
    url: str
    confidence: float = 1.0
    
    def is_valid(self) -> bool:
        """Check if scenario is valid"""
        if not self.steps or len(self.steps) < 3:
            return False
        if any(not step.strip() for step in self.steps):
            return False
        return True


class MultiAgentOrchestrator:
    """
    Multi-Agent Orchestrator using LangGraph
    
    This orchestrator coordinates 6 specialized agents:
    1. DOM Analysis Agent - Analyzes and classifies interactions
    2. Classifier Agent - Separates interactions by type
    3. Hover Agent - Generates hover scenarios
    4. Popup Agent - Generates popup scenarios
    5. Gherkin Agent - Formats scenarios properly
    6. Validator Agent - Validates quality and correctness
    """
    
    def __init__(self, ollama_url: str = None, model: str = None):
        self.workflow = MultiAgentWorkflow(ollama_url, model)
        logger.info("✓ Multi-Agent Orchestrator initialized with LangGraph workflow")
    
    async def generate_scenarios(
        self,
        url: str,
        interactions: List[Any],
        dom_structure: Dict[str, Any]
    ) -> List[TestScenario]:
        """
        Generate test scenarios using multi-agent workflow
        
        Args:
            url: Website URL
            interactions: List of detected interactions
            dom_structure: Analyzed DOM structure
            
        Returns:
            List of TestScenario objects
        """
        logger.info("🤖 Starting Multi-Agent Workflow for scenario generation...")
        
        try:
            # Execute the multi-agent workflow
            validated_scenarios = await self.workflow.generate_scenarios(
                url=url,
                interactions=interactions,
                dom_structure=dom_structure
            )
            
            # Convert to TestScenario format (for compatibility with existing code)
            test_scenarios = []
            for scenario in validated_scenarios:
                test_scenario = TestScenario(
                    feature_name=scenario.feature_name,
                    scenario_name=scenario.scenario_name,
                    steps=scenario.steps,
                    scenario_type=scenario.scenario_type,
                    url=scenario.url,
                    confidence=scenario.confidence
                )
                test_scenarios.append(test_scenario)
            
            logger.info(f"✅ Multi-Agent Workflow generated {len(test_scenarios)} scenarios")
            
            # Log agent statistics
            self._log_statistics(test_scenarios)
            
            return test_scenarios
            
        except Exception as e:
            logger.error(f"❌ Multi-Agent Workflow failed: {str(e)}")
            raise
    
    def _log_statistics(self, scenarios: List[TestScenario]):
        """Log statistics about generated scenarios"""
        hover_count = sum(1 for s in scenarios if s.scenario_type == 'hover')
        popup_count = sum(1 for s in scenarios if s.scenario_type == 'popup')
        avg_confidence = sum(s.confidence for s in scenarios) / len(scenarios) if scenarios else 0
        
        logger.info("📊 Multi-Agent Statistics:")
        logger.info(f"  - Total Scenarios: {len(scenarios)}")
        logger.info(f"  - Hover Scenarios: {hover_count}")
        logger.info(f"  - Popup Scenarios: {popup_count}")
        logger.info(f"  - Average Confidence: {avg_confidence:.2f}")
