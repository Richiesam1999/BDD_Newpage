"""
Multi-Agent Workflow (Simplified - No LangGraph dependency)
Orchestrates specialized agents in a pipeline

Note: This is a simplified implementation that doesn't require LangGraph.
For production use with LangGraph, install: pip install langgraph==0.0.20
"""
import logging
from typing import List, Dict, Any

from ..agents.dom_agent import DOMAnalysisAgent
from ..agents.classifier_agent import InteractionClassifierAgent
from ..agents.hover_agent import HoverAgent
from ..agents.popup_agent import PopupAgent
from ..agents.gherkin_agent import GherkinAgent
from ..agents.validator_agent import ValidatorAgent
from ..llm_client import OllamaClient

logger = logging.getLogger(__name__)


class MultiAgentWorkflow:
    """
    Simplified multi-agent workflow for BDD test generation
    (No LangGraph dependency - sequential execution)
    """
    
    def __init__(self, ollama_url: str = None, model: str = None):
        self.llm = OllamaClient(ollama_url, model)
        
        # Initialize agents
        self.dom_agent = DOMAnalysisAgent(self.llm)
        self.classifier_agent = InteractionClassifierAgent()
        self.hover_agent = HoverAgent(self.llm)
        self.popup_agent = PopupAgent(self.llm)
        self.gherkin_agent = GherkinAgent(self.llm)
        self.validator_agent = ValidatorAgent()
        
        logger.info("✓ Multi-Agent Workflow initialized (Simplified mode)")
    
    async def _dom_analysis_node(self, state: Dict) -> Dict:
        """DOM Analysis Agent Node"""
        logger.info("🔬 [Workflow] DOM Analysis Agent...")
        logger.debug(f"  Input: {len(state.get('raw_interactions', []))} raw interactions")
        
        try:
            classified = await self.dom_agent.analyze(
                state['raw_interactions'],
                state['dom_structure']
            )
            logger.debug(f"  Output: {len(classified)} classified interactions")
            return {"classified_interactions": classified}
        except Exception as e:
            logger.error(f"DOM Analysis failed: {str(e)}")
            return {"error": str(e), "classified_interactions": []}
    
    async def _classify_node(self, state: Dict) -> Dict:
        """Classifier Agent Node"""
        logger.info("📊 [Workflow] Classifier Agent...")
        logger.debug(f"  Input: {len(state.get('classified_interactions', []))} classified interactions")
        
        try:
            categorized = self.classifier_agent.classify(state['classified_interactions'])
            logger.debug(f"  Output: hover={len(categorized.get('hover', []))}, popup={len(categorized.get('popup', []))}")
            return {"categorized": categorized}
        except Exception as e:
            logger.error(f"Classification failed: {str(e)}")
            return {"error": str(e), "categorized": {'hover': [], 'popup': []}}
    
    async def _hover_node(self, state: Dict) -> Dict:
        """Hover Agent Node"""
        logger.info("🖱️  [Workflow] Hover Agent...")
        
        try:
            hover_items = state['categorized'].get('hover', [])
            scenarios = await self.hover_agent.generate_scenarios(hover_items, state['url'])
            return {"hover_scenarios": scenarios}
        except Exception as e:
            logger.error(f"Hover generation failed: {str(e)}")
            return {"error": str(e), "hover_scenarios": []}
    
    async def _popup_node(self, state: Dict) -> Dict:
        """Popup Agent Node"""
        logger.info("🪟 [Workflow] Popup Agent...")
        
        try:
            popup_items = state['categorized'].get('popup', [])
            scenarios = await self.popup_agent.generate_scenarios(popup_items, state['url'])
            return {"popup_scenarios": scenarios}
        except Exception as e:
            logger.error(f"Popup generation failed: {str(e)}")
            return {"error": str(e), "popup_scenarios": []}
    
    async def _gherkin_node(self, state: Dict) -> Dict:
        """Gherkin Agent Node"""
        logger.info("📝 [Workflow] Gherkin Agent...")
        
        try:
            scenarios = await self.gherkin_agent.format_scenarios(
                state['hover_scenarios'],
                state['popup_scenarios'],
                state['url']
            )
            return {"gherkin_scenarios": scenarios}
        except Exception as e:
            logger.error(f"Gherkin formatting failed: {str(e)}")
            return {"error": str(e), "gherkin_scenarios": []}
    
    async def _validate_node(self, state: Dict) -> Dict:
        """Validator Agent Node"""
        logger.info("✅ [Workflow] Validator Agent...")
        
        try:
            validated = self.validator_agent.validate_scenarios(state['gherkin_scenarios'])
            return {"validated_scenarios": validated}
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            return {"error": str(e), "validated_scenarios": state['gherkin_scenarios']}
    
    async def generate_scenarios(
        self,
        url: str,
        interactions: List[Any],
        dom_structure: Dict[str, Any]
    ) -> List:
        """
        Execute the multi-agent workflow
        
        Args:
            url: Website URL
            interactions: Raw interactions from element detector
            dom_structure: Analyzed DOM structure
            
        Returns:
            List of validated Gherkin scenarios
        """
        logger.info("🚀 Starting Multi-Agent Workflow...")
        
        # Initialize state
        state = {
            "url": url,
            "raw_interactions": interactions,
            "dom_structure": dom_structure,
            "classified_interactions": [],
            "categorized": {},
            "hover_scenarios": [],
            "popup_scenarios": [],
            "gherkin_scenarios": [],
            "validated_scenarios": [],
            "error": ""
        }
        
        # Execute workflow
        try:
            # Run through all nodes sequentially, updating state
            result = await self._dom_analysis_node(state)
            state.update(result)
            
            result = await self._classify_node(state)
            state.update(result)
            
            result = await self._hover_node(state)
            state.update(result)
            
            result = await self._popup_node(state)
            state.update(result)
            
            result = await self._gherkin_node(state)
            state.update(result)
            
            result = await self._validate_node(state)
            state.update(result)
            
            final_scenarios = state.get('validated_scenarios', [])
            
            logger.info(f"✅ Workflow complete: {len(final_scenarios)} validated scenarios")
            
            return final_scenarios
            
        except Exception as e:
            logger.error(f"❌ Workflow failed: {str(e)}")
            raise
