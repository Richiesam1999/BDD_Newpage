#V2
import asyncio
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
from urllib.parse import urlparse

# Import our modules
from src.browser.automation import BrowserAutomation
from src.browser.element_detector import ElementDetector
from src.analyzer.dom_analyzer import DOMAnalyzer
from src.analyzer.interaction_mapper import InteractionMapper
from src.ai.agent_orchestrator import AgentOrchestrator
from src.ai.llm_client import OllamaClient
from src.generator.gherkin_generator import GherkinGenerator
from src.cache.storage import DOMCache
from config import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BDDTestGeneratorCLI:
    """Main CLI application controller"""
    
    def __init__(self, args):
        self.args = args
        self.cache = DOMCache() if not args.no_cache else None
        self.browser = None
        self.output_dir = config.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing browser automation...")
        
        # Check Ollama availability
        ollama_client = OllamaClient()
        is_healthy = await ollama_client.check_health()
        if not is_healthy:
            logger.error("❌ Ollama is not running or not accessible")
            logger.error(f"   Please ensure Ollama is running at {config.OLLAMA_URL}")
            logger.error("   Run: ollama serve")
            sys.exit(1)
        
        models = await ollama_client.list_models()
        if config.OLLAMA_MODEL not in models:
            logger.warning(f"⚠️  Model '{config.OLLAMA_MODEL}' not found")
            logger.info(f"   Available models: {', '.join(models) if models else 'None'}")
            logger.info(f"   Run: ollama pull {config.OLLAMA_MODEL}")
            sys.exit(1)
        
        logger.info(f"✓ Ollama connected (model: {config.OLLAMA_MODEL})")
        
        # Initialize browser
        self.browser = await BrowserAutomation.create(
            headless=not self.args.show_browser,
            timeout=self.args.timeout * 1000
        )
        logger.info("✓ Browser initialized")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")
    
    async def generate_tests(self, url: str) -> Optional[str]:
        """
        Main orchestration method - generates BDD tests for given URL
        
        Returns:
            Path to generated .feature file
        """
        logger.info(f"🚀 Starting test generation for: {url}")
        start_time = datetime.now()
        
        try:
            # Step 1: Check cache
            if self.cache:
                cached = await self.cache.get_cached_analysis(url)
                if cached and cached.get('feature_content'):
                    logger.info("✓ Using cached results")
                    return self._save_from_cache(cached)
            
            # Step 2: Navigate to page
            logger.info("📄 Loading webpage...")
            await self.browser.navigate(url)
            await asyncio.sleep(2)  # Wait for dynamic content
            logger.info("✓ Page loaded")
            
            # Step 3: Detect interactive elements
            logger.info("🔍 Detecting interactive elements...")
            detector = ElementDetector(self.browser)

            # 3a: Check for any popup that appeared automatically on page load
            initial_popup = await detector.detect_initial_popup(url)
            interaction_mapper = InteractionMapper()
            if initial_popup:
                interaction_mapper.add_interaction(initial_popup)
            
            hover_elements = await detector.find_hoverable_elements()
            logger.info(f"✓ Found {len(hover_elements)} hoverable elements")
            
            popup_triggers = await detector.detect_popup_triggers()
            logger.info(f"✓ Found {len(popup_triggers)} popup triggers")
            
            if not hover_elements and not popup_triggers and not interaction_mapper.get_popup_interactions():
                logger.warning("⚠️  No interactive elements detected")
                return self._generate_empty_feature(url)
            
            # Step 4: Simulate interactions
            logger.info("🎭 Simulating interactions...")
            # Note: interaction_mapper may already contain initial popup
            # interactions added above.
            
            # Test hover interactions (limited to avoid timeout)
            for i, element in enumerate(hover_elements[:5], 1):
                logger.info(f"   Testing hover {i}/{min(5, len(hover_elements))}")
                interaction = await detector.simulate_hover_interaction(element)
                if interaction:
                    interaction_mapper.add_interaction(interaction)
            
            # Test popup interactions (limited to avoid timeout)
            for i, trigger in enumerate(popup_triggers[:3], 1):
                logger.info(f"   Testing popup {i}/{min(3, len(popup_triggers))}")
                interaction = await detector.simulate_popup_interaction(trigger)
                if interaction:
                    interaction_mapper.add_interaction(interaction)
            
            all_interactions = interaction_mapper.get_all_interactions()
            logger.info(f"✓ Captured {len(all_interactions)} interactions")

            # Optional advanced popup detection (CTA exploration)
            popup_interactions = interaction_mapper.get_popup_interactions()
            if (not popup_interactions and
                getattr(config, "ENABLE_ADVANCED_POPUP_DETECTION", False)):
                logger.info("⚙️ No popups from primary strategies, running advanced popup scan...")
                advanced_popups = await detector.find_advanced_popup_interactions()
                for inter in advanced_popups:
                    interaction_mapper.add_interaction(inter)
                all_interactions = interaction_mapper.get_all_interactions()
                logger.info(f"✓ Advanced popup scan captured {len(advanced_popups)} popup interaction(s)")
            
            # Optional advanced hover detection for modern navs (e.g., Apple / Nike).
            if (not all_interactions and
                getattr(config, "ENABLE_ADVANCED_HOVER_DETECTION", False)):
                logger.info("⚙️ No interactions from primary strategies, running advanced hover scan...")
                advanced = await detector.find_advanced_hover_interactions()
                for inter in advanced:
                    interaction_mapper.add_interaction(inter)
                all_interactions = interaction_mapper.get_all_interactions()
                logger.info(f"✓ Advanced scan captured {len(advanced)} additional interactions")
            
            if not all_interactions:
                logger.warning("⚠️  No meaningful interactions detected")
                return self._generate_empty_feature(url)
            
            # Step 5: Analyze DOM
            logger.info("🔬 Analyzing page structure...")
            dom_analyzer = DOMAnalyzer()
            page_content = await self.browser.get_page_content()
            dom_structure = dom_analyzer.analyze(page_content, url)
            logger.info(f"✓ Page type: {dom_structure['page_type']}")
            
            # Step 6: Generate scenarios using AI
            logger.info("🤖 Generating test scenarios with AI...")
            orchestrator = AgentOrchestrator()
            raw_scenarios = await orchestrator.generate_scenarios(
                url=url,
                interactions=all_interactions,
                dom_structure=dom_structure
            )
            logger.info(f"✓ Generated {len(raw_scenarios)} raw scenarios")
            
            # Step 6.5: Quality filter
            logger.info("🔍 Applying quality filters...")
            from src.generator.quality_filter import QualityFilter
            scenarios = QualityFilter.process_scenarios(raw_scenarios)
            logger.info(f"✓ {len(scenarios)} scenarios passed quality check")
            
            # Step 7: Generate Gherkin
            logger.info("📝 Creating Gherkin .feature file...")
            gherkin_generator = GherkinGenerator()
            feature_content = gherkin_generator.generate_feature_file(url, scenarios)
            
            # Step 8: Save output
            output_path = self._save_feature_file(url, feature_content)
            
            # Step 9: Cache results
            if self.cache:
                await self.cache.store_analysis(url, all_interactions, scenarios, feature_content)
            
            # Report completion
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Completed in {elapsed:.2f} seconds")
            
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Error: {str(e)}", exc_info=True)
            raise
    
    def _save_feature_file(self, url: str, content: str) -> Path:
        """Save Gherkin content to .feature file"""
        if self.args.output:
            filename = self.args.output
            if not filename.endswith('.feature'):
                filename += '.feature'
        else:
            domain = urlparse(url).netloc.replace('www.', '').replace('.', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{domain}_{timestamp}.feature"
        
        output_path = self.output_dir / filename
        output_path.write_text(content, encoding='utf-8')
        
        return output_path
    
    def _save_from_cache(self, cached_data: dict) -> Path:
        """Save cached results"""
        return self._save_feature_file(cached_data['url'], cached_data['feature_content'])
    
    def _generate_empty_feature(self, url: str) -> Path:
        """Generate empty feature when no interactions found"""
        generator = GherkinGenerator()
        content = generator._generate_empty_feature(url)
        return self._save_feature_file(url, content)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Generate BDD tests for websites with hover and popup interactions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py https://www.nike.com
  python main.py https://www.apple.com --output apple_tests
  python main.py https://www.tivdak.com/patient-stories/ --verbose
  python main.py https://www.nike.com --no-cache --show-browser
        """
    )
    
    parser.add_argument('url', type=str, help='Website URL to analyze')
    parser.add_argument('-o', '--output', type=str, help='Custom output filename', default=None)
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-cache', action='store_true', help='Disable caching')
    parser.add_argument('--show-browser', action='store_true', help='Show browser window')
    parser.add_argument('--timeout', type=int, default=30, help='Browser timeout (seconds)')
    
    return parser.parse_args()


async def main():
    """Main async entry point"""
    args = parse_arguments()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate URL
    if not args.url.startswith(('http://', 'https://')):
        logger.error("❌ Invalid URL. Must start with http:// or https://")
        sys.exit(1)
    
    # Initialize CLI
    cli = BDDTestGeneratorCLI(args)
    
    try:
        await cli.initialize()
        output_path = await cli.generate_tests(args.url)
        
        if output_path:
            print(f"\n{'='*70}")
            print(f"✅ SUCCESS!")
            print(f"{'='*70}")
            print(f"📄 Generated: {output_path}")
            print(f"\n💡 Usage:")
            print(f"   - Behave (Python): behave {output_path}")
            print(f"   - Cucumber: cucumber {output_path}")
            print(f"{'='*70}\n")
        else:
            print("\n⚠️  Generation completed with warnings. Check logs.\n")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n⚠️  Cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)
    finally:
        await cli.cleanup()


if __name__ == "__main__":
    # Fix for Windows: Set event loop policy to support subprocess operations (required by Playwright)
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())