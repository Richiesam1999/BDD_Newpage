"""
Quick test for multi-agent workflow
"""
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)

# Mock interaction for testing
class MockElement:
    def __init__(self):
        self.text = "Test Button"
        self.tag = "button"
    
    def get_description(self):
        return "Test button element"

class MockInteraction:
    def __init__(self):
        self.trigger_element = MockElement()
        self.action_type = "hover"
        self.popup_appeared = False
        self.revealed_elements = []
        self.url_after = None

async def test_workflow():
    from src.ai.graph.workflow import MultiAgentWorkflow
    
    print("\n" + "="*80)
    print("Testing Multi-Agent Workflow")
    print("="*80)
    
    # Create workflow
    workflow = MultiAgentWorkflow()
    
    # Create mock data
    interactions = [MockInteraction()]
    dom_structure = {"page_type": "general"}
    url = "https://example.com"
    
    print(f"\nInput: {len(interactions)} interactions")
    
    # Run workflow
    try:
        scenarios = await workflow.generate_scenarios(
            url=url,
            interactions=interactions,
            dom_structure=dom_structure
        )
        
        print(f"\nOutput: {len(scenarios)} scenarios")
        
        if scenarios:
            print("\nFirst scenario:")
            print(f"  Feature: {scenarios[0].feature_name}")
            print(f"  Scenario: {scenarios[0].scenario_name}")
            print(f"  Steps: {len(scenarios[0].steps)}")
        
        print("\n✅ Test passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workflow())
