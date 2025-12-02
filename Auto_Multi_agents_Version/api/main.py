import asyncio
import sys
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from config import config
from src.browser.automation import BrowserAutomation
from src.browser.element_detector import ElementDetector
from src.analyzer.dom_analyzer import DOMAnalyzer
from src.analyzer.interaction_mapper import InteractionMapper
from src.ai.agent_orchestrator import AgentOrchestrator
from src.generator.gherkin_generator import GherkinGenerator
from src.generator.quality_filter import QualityFilter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI(title="BDD Test Generator API")

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="playwright")


class GenerateRequest(BaseModel):
    url: str


class GenerateResponse(BaseModel):
 
    success: bool
    url: str
    feature_content: str
    filename: str
    message: str = ""


def _run_analysis_sync(url: str) -> Dict[str, Any]:
    logger.info(f"[Thread] Starting analysis for URL: {url}")
    
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        logger.info(f"[Thread] Event loop created, starting async analysis...")
        result = loop.run_until_complete(_run_analysis_async(url))
        logger.info(f"[Thread] Analysis completed successfully")
        return result
    except Exception as e:
        logger.error(f"[Thread] Analysis failed with error: {e}", exc_info=True)
        raise
    finally:
        loop.close()
        asyncio.set_event_loop(None)
        logger.info(f"[Thread] Event loop closed")


async def _run_analysis_async(url: str) -> Dict[str, Any]:
    """The actual async analysis logic - returns feature content directly"""
    browser = None
    
    try:
        logger.info(f"[Step 0] Initializing browser automation...")
        browser = await BrowserAutomation.create()
        logger.info(f"[Step 0] Browser initialized successfully")

        # Step 1: Navigate to page
        logger.info(f"[Step 1] Navigating to URL: {url}")
        await browser.navigate(url)
        logger.info(f"[Step 1] Navigation complete, waiting 2 seconds...")
        await asyncio.sleep(2)
        logger.info(f"[Step 1] Page loaded successfully")

        # Step 2: Detect interactions
        logger.info(f"[Step 2] Starting interaction detection...")
        detector = ElementDetector(browser)
        interaction_mapper = InteractionMapper()

        # Initial popup on page load
        logger.info(f"[Step 2a] Detecting initial popup...")
        initial_popup = await detector.detect_initial_popup(url)
        if initial_popup:
            interaction_mapper.add_interaction(initial_popup)
            logger.info(f"[Step 2a] Initial popup detected and added")
        else:
            logger.info(f"[Step 2a] No initial popup detected")

        logger.info(f"[Step 2b] Finding hoverable elements...")
        hover_elements = await detector.find_hoverable_elements()
        logger.info(f"[Step 2b] Found {len(hover_elements)} hoverable elements")

        logger.info(f"[Step 2c] Detecting popup triggers...")
        popup_triggers = await detector.detect_popup_triggers()
        logger.info(f"[Step 2c] Found {len(popup_triggers)} popup triggers")

        # Simulate interactions
        logger.info(f"[Step 2d] Simulating hover interactions (max 5)...")
        hover_count = 0
        for i, element in enumerate(hover_elements[:5], 1):
            logger.info(f"[Step 2d] Simulating hover {i}/5...")
            interaction = await detector.simulate_hover_interaction(element)
            if interaction:
                interaction_mapper.add_interaction(interaction)
                hover_count += 1
        logger.info(f"[Step 2d] Completed {hover_count} hover interactions")

        logger.info(f"[Step 2e] Simulating popup interactions (max 3)...")
        popup_count = 0
        for i, trigger in enumerate(popup_triggers[:3], 1):
            logger.info(f"[Step 2e] Simulating popup {i}/3...")
            interaction = await detector.simulate_popup_interaction(trigger)
            if interaction:
                interaction_mapper.add_interaction(interaction)
                popup_count += 1
        logger.info(f"[Step 2e] Completed {popup_count} popup interactions")

        all_interactions = interaction_mapper.get_all_interactions()
        logger.info(f"[Step 2] Total interactions detected: {len(all_interactions)}")

        if not all_interactions:
            # Generate an "empty" feature file noting lack of interactions
            logger.info(f"[Step 3] No interactions found, generating empty feature file...")
            ggen = GherkinGenerator()
            feature_content = ggen._generate_empty_feature(url)
            logger.info(f"[Step 3] Empty feature file generated")
        else:
            # Step 3: DOM analysis
            logger.info(f"[Step 3] Starting DOM analysis...")
            dom_analyzer = DOMAnalyzer()
            page_content = await browser.get_page_content()
            logger.info(f"[Step 3] Page content retrieved ({len(page_content)} chars)")
            dom_structure = dom_analyzer.analyze(page_content, url)
            logger.info(f"[Step 3] DOM analysis complete")

            # Step 4: Scenario generation via agent orchestrator
            logger.info(f"[Step 4] Starting AI scenario generation...")
            logger.info(f"[Step 4] This may take several minutes...")
            orchestrator = AgentOrchestrator()
            raw_scenarios = await orchestrator.generate_scenarios(
                url=url,
                interactions=all_interactions,
                dom_structure=dom_structure,
            )
            logger.info(f"[Step 4] Generated {len(raw_scenarios)} raw scenarios")

            # Step 5: Quality filter
            logger.info(f"[Step 5] Applying quality filter...")
            scenarios = QualityFilter.process_scenarios(raw_scenarios)
            logger.info(f"[Step 5] After filtering: {len(scenarios)} scenarios")

            # Step 6: Gherkin generation
            logger.info(f"[Step 6] Generating Gherkin feature file...")
            ggen = GherkinGenerator()
            feature_content = ggen.generate_feature_file(url, scenarios)
            logger.info(f"[Step 6] Feature file generated ({len(feature_content)} chars)")

        # Step 7: Generate filename and optionally save
        logger.info(f"[Step 7] Saving feature file...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_domain = (
            url.split("//", 1)[-1]
            .split("/", 1)[0]
            .replace("www.", "")
            .replace(".", "_")
        )
        filename = f"{safe_domain}_{timestamp}.feature"
        
        # Optionally save to file
        output_path = config.OUTPUT_DIR
        output_path.mkdir(parents=True, exist_ok=True)
        output_path = output_path / filename
        output_path.write_text(feature_content, encoding="utf-8")
        logger.info(f"[Step 7] Feature file saved: {output_path}")

        logger.info(f"[SUCCESS] Analysis completed for {url}")
        return {
            "success": True,
            "url": url,
            "feature_content": feature_content,
            "filename": filename,
            "message": "BDD tests generated successfully"
        }

    except Exception as e:  # noqa: BLE001
        logger.error(f"[ERROR] Analysis failed: {e}", exc_info=True)
        return {
            "success": False,
            "url": url,
            "feature_content": "",
            "filename": "",
            "message": f"Error: {str(e)}"
        }
    finally:
        if browser:
            logger.info(f"[Cleanup] Closing browser...")
            await browser.close()
            logger.info(f"[Cleanup] Browser closed")


@app.post("/generate", response_model=GenerateResponse)
async def generate_tests(request: GenerateRequest):
    url = request.url
    logger.info(f"=== NEW REQUEST: POST /generate for URL: {url} ===")
    
    if not url.startswith(('http://', 'https://')):
        logger.error(f"Invalid URL format: {url}")
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
    
    try:
        if sys.platform == "win32":
            logger.info(f"Running on Windows - using thread executor")
            # Submit to thread pool executor to run in a thread with proper event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(_executor, _run_analysis_sync, url)
        else:
            logger.info(f"Running on {sys.platform} - using direct async execution")
            result = await _run_analysis_async(url)
        
        logger.info(f"=== REQUEST COMPLETED: {url} - Success: {result.get('success')} ===")
        return GenerateResponse(**result)
    
    except Exception as e:
        logger.error(f"=== REQUEST FAILED: {url} - Error: {str(e)} ===", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate tests: {str(e)}"
        )


# @app.get("/")
# async def root():
#     """Root endpoint with API information"""
#     return {
#         "name": "BDD Test Generator API",
#         "version": "1.0",
#         "endpoints": {
#             "POST /generate": "Generate BDD tests from a URL. Returns feature file content directly.",
#         },
#         "example": {
#             "url": "/generate",
#             "method": "POST",
#             "body": {"url": "https://example.com"}
#         }
#     }
