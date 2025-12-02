"""
Comparison Script - Single Agent vs Multi-Agent
Run this to see the difference between the two approaches
"""
import asyncio
import sys
import logging
from datetime import datetime

from src.browser.automation import BrowserAutomation
from src.browser.element_detector import ElementDetector
from src.analyzer.dom_analyzer import DOMAnalyzer
from src.analyzer.interaction_mapper import InteractionMapper
from src.ai.agent_orchestrator import AgentOrchestrator
from src.ai.multi_agent_orchestrator import MultiAgentOrchestrator
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def compare_approaches(url: str):
    """Compare single-agent vs multi-agent approaches"""
    
    print("\n" + "="*80)
    print("🔬 COMPARING SINGLE-AGENT vs MULTI-AGENT APPROACHES")
    print("="*80)
    print(f"URL: {url}\n")
    
    # Initialize browser
    browser = await BrowserAutomation.create(headless=True)
    
    try:
        # Navigate and detect interactions
        print("📄 Loading webpage...")
        await browser.navigate(url)
        await asyncio.sleep(2)
        
        print("🔍 Detecting interactions...")
        detector = ElementDetector(browser)
        interaction_mapper = InteractionMapper()
        
        # Detect initial popup
        initial_popup = await detector.detect_initial_popup(url)
        if initial_popup:
            interaction_mapper.add_interaction(initial_popup)
        
        # Find hover elements
        hover_elements = await detector.find_hoverable_elements()
        for element in hover_elements[:3]:  # Limit for comparison
            interaction = await detector.simulate_hover_interaction(element)
            if interaction:
                interaction_mapper.add_interaction(interaction)
        
        # Find popup triggers
        popup_triggers = await detector.detect_popup_triggers()
        for trigger in popup_triggers[:2]:  # Limit for comparison
            interaction = await detector.simulate_popup_interaction(trigger)
            if interaction:
                interaction_mapper.add_interaction(interaction)
        
        all_interactions = interaction_mapper.get_all_interactions()
        print(f"✓ Captured {len(all_interactions)} interactions\n")
        
        # Analyze DOM
        dom_analyzer = DOMAnalyzer()
        page_content = await browser.get_page_content()
        dom_structure = dom_analyzer.analyze(page_content, url)
        
        # ========== SINGLE-AGENT APPROACH ==========
        print("\n" + "-"*80)
        print("🤖 SINGLE-AGENT APPROACH")
        print("-"*80)
        
        start_single = datetime.now()
        single_orchestrator = AgentOrchestrator()
        single_scenarios = await single_orchestrator.generate_scenarios(
            url=url,
            interactions=all_interactions,
            dom_structure=dom_structure
        )
        time_single = (datetime.now() - start_single).total_seconds()
        
        print(f"\n📊 Single-Agent Results:")
        print(f"  - Scenarios Generated: {len(single_scenarios)}")
        print(f"  - Time Taken: {time_single:.2f} seconds")
        print(f"  - Average per scenario: {time_single/len(single_scenarios):.2f}s" if single_scenarios else "")
        
        # ========== MULTI-AGENT APPROACH ==========
        print("\n" + "-"*80)
        print("🤖🤖🤖 MULTI-AGENT APPROACH (LangGraph)")
        print("-"*80)
        
        start_multi = datetime.now()
        multi_orchestrator = MultiAgentOrchestrator()
        multi_scenarios = await multi_orchestrator.generate_scenarios(
            url=url,
            interactions=all_interactions,
            dom_structure=dom_structure
        )
        time_multi = (datetime.now() - start_multi).total_seconds()
        
        print(f"\n📊 Multi-Agent Results:")
        print(f"  - Scenarios Generated: {len(multi_scenarios)}")
        print(f"  - Time Taken: {time_multi:.2f} seconds")
        print(f"  - Average per scenario: {time_multi/len(multi_scenarios):.2f}s" if multi_scenarios else "")
        
        # ========== COMPARISON ==========
        print("\n" + "="*80)
        print("📈 COMPARISON SUMMARY")
        print("="*80)
        
        print(f"\n{'Metric':<30} {'Single-Agent':<20} {'Multi-Agent':<20}")
        print("-"*70)
        print(f"{'Total Scenarios':<30} {len(single_scenarios):<20} {len(multi_scenarios):<20}")
        print(f"{'Time (seconds)':<30} {time_single:<20.2f} {time_multi:<20.2f}")
        print(f"{'Avg Confidence':<30} {sum(s.confidence for s in single_scenarios)/len(single_scenarios) if single_scenarios else 0:<20.2f} {sum(s.confidence for s in multi_scenarios)/len(multi_scenarios) if multi_scenarios else 0:<20.2f}")
        
        # Quality comparison
        single_valid = sum(1 for s in single_scenarios if s.is_valid())
        multi_valid = sum(1 for s in multi_scenarios if s.is_valid())
        
        print(f"{'Valid Scenarios':<30} {single_valid:<20} {multi_valid:<20}")
        print(f"{'Quality Rate':<30} {single_valid/len(single_scenarios)*100 if single_scenarios else 0:<20.1f}% {multi_valid/len(multi_scenarios)*100 if multi_scenarios else 0:<20.1f}%")
        
        # Show sample scenarios
        print("\n" + "="*80)
        print("📝 SAMPLE SCENARIOS")
        print("="*80)
        
        if single_scenarios:
            print("\n🤖 Single-Agent Sample:")
            print(f"Feature: {single_scenarios[0].feature_name}")
            print(f"Scenario: {single_scenarios[0].scenario_name}")
            for step in single_scenarios[0].steps[:3]:
                print(f"  {step}")
        
        if multi_scenarios:
            print("\n🤖🤖🤖 Multi-Agent Sample:")
            print(f"Feature: {multi_scenarios[0].feature_name}")
            print(f"Scenario: {multi_scenarios[0].scenario_name}")
            for step in multi_scenarios[0].steps[:3]:
                print(f"  {step}")
        
        print("\n" + "="*80)
        print("✅ COMPARISON COMPLETE")
        print("="*80)
        
        # Recommendation
        if multi_valid > single_valid:
            print("\n💡 Recommendation: Use MULTI-AGENT approach for better quality")
        elif time_single < time_multi * 0.7:
            print("\n💡 Recommendation: Use SINGLE-AGENT for faster results")
        else:
            print("\n💡 Recommendation: Both approaches are comparable")
        
    finally:
        await browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python compare_agents.py <URL>")
        print("Example: python compare_agents.py https://www.tivdak.com/patient-stories/")
        sys.exit(1)
    
    url = sys.argv[1]
    
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(compare_approaches(url))
