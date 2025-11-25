"""
Browser Automation using Playwright
Handles page navigation, content extraction, and JavaScript execution
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from config import config

logger = logging.getLogger(__name__)


class BrowserAutomation:
    """Manages browser automation with Playwright"""
    
    def __init__(self, browser: Browser, context: BrowserContext, page: Page):
        self.browser = browser
        self.context = context
        self.page = page
        self._playwright = None
    
    @classmethod
    async def create(cls, headless: bool = None, timeout: int = None) -> 'BrowserAutomation':
        """Factory method to create BrowserAutomation instance"""
        headless = headless if headless is not None else config.HEADLESS
        timeout = timeout if timeout is not None else config.BROWSER_TIMEOUT
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=headless)
        
        context = await browser.new_context(
            viewport={'width': config.VIEWPORT_WIDTH, 'height': config.VIEWPORT_HEIGHT},
            user_agent=config.USER_AGENT
        )
        
        page = await context.new_page()
        page.set_default_timeout(timeout)
        
        instance = cls(browser, context, page)
        instance._playwright = playwright
        
        logger.info(f"Browser initialized (headless={headless})")
        return instance
    
    async def navigate(self, url: str) -> None:
        """Navigate to URL and wait for page load"""
        try:
            logger.info(f"Navigating to: {url}")
            await self.page.goto(url, wait_until="networkidle", timeout=config.BROWSER_TIMEOUT)
            logger.info("Page loaded successfully")
        except Exception as e:
            logger.error(f"Navigation failed: {str(e)}")
            raise
    
    async def get_page_content(self) -> str:
        """Get full HTML content of current page"""
        return await self.page.content()
    
    async def get_page_title(self) -> str:
        """Get page title"""
        return await self.page.title()
    
    async def get_current_url(self) -> str:
        """Get current URL"""
        return self.page.url
    
    async def take_screenshot(self, path: str) -> None:
        """Take screenshot of current page"""
        await self.page.screenshot(path=path, full_page=True)
        logger.debug(f"Screenshot saved: {path}")
    
    async def execute_script(self, script: str) -> Any:
        """Execute JavaScript in page context"""
        return await self.page.evaluate(script)
    
    async def get_all_interactive_elements(self) -> List[Dict[str, Any]]:
        """
        Get all potentially interactive elements on the page
        Returns list of element info dictionaries
        """
        script = """
        () => {
            const elements = [];
            const selectors = [
                'a', 'button', '[role="button"]', 
                'nav a', 'nav button', '.menu', '.dropdown',
                '[aria-haspopup]', '[onclick]', '[onmouseover]'
            ];
            
            const allElements = document.querySelectorAll(selectors.join(','));
            
            allElements.forEach((el, idx) => {
                const rect = el.getBoundingClientRect();
                const styles = window.getComputedStyle(el);
                
                // Only include visible elements
                if (rect.width > 0 && rect.height > 0 && styles.display !== 'none') {
                    elements.push({
                        index: idx,
                        tag: el.tagName.toLowerCase(),
                        text: el.innerText?.trim().substring(0, 100) || '',
                        id: el.id || '',
                        className: el.className || '',
                        href: el.href || '',
                        role: el.getAttribute('role') || '',
                        ariaLabel: el.getAttribute('aria-label') || '',
                        ariaHasPopup: el.getAttribute('aria-haspopup') || '',
                        hasHoverCSS: false,  // Will be determined by CSS analysis
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    });
                }
            });
            
            return elements;
        }
        """
        
        elements = await self.execute_script(script)
        logger.debug(f"Found {len(elements)} interactive elements")
        return elements
    
    async def get_element_by_text(self, text: str, tag: str = None):
        """Get element locator by visible text"""
        selector = f"{tag}:has-text('{text}')" if tag else f":has-text('{text}')"
        return self.page.locator(selector).first
    
    async def hover_element(self, selector: str = None, element_locator = None) -> None:
        """Hover over an element"""
        if element_locator:
            await element_locator.hover()
        elif selector:
            await self.page.locator(selector).first.hover()
        else:
            raise ValueError("Either selector or element_locator must be provided")
        
        await asyncio.sleep(0.3)  # Wait for hover effects
    
    async def click_element(self, selector: str = None, element_locator = None) -> None:
        """Click an element"""
        if element_locator:
            await element_locator.click()
        elif selector:
            await self.page.locator(selector).first.click()
        else:
            raise ValueError("Either selector or element_locator must be provided")
        
        await asyncio.sleep(0.3)  # Wait for click effects
    
    async def get_visible_elements(self) -> List[Dict]:
        """Get all currently visible elements (richer metadata for nav diffing).

        This is used by ElementDetector to diff before/after states around
        hover/click and discover newly visible navigation links.
        """
        script = """
        () => {
            const elements = [];
            const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 0;

            document.querySelectorAll('*').forEach(el => {
                const rect = el.getBoundingClientRect();
                const styles = window.getComputedStyle(el);

                // Basic visibility check: non-zero size, not display:none/visibility:hidden
                if (rect.width <= 0 || rect.height <= 0) return;
                if (styles.display === 'none' || styles.visibility === 'hidden') return;

                // Only consider elements that intersect the viewport vertically
                if (rect.bottom < 0 || rect.top > viewportHeight) return;

                const tag = el.tagName.toLowerCase();
                const text = (el.innerText || '').trim().substring(0, 80);

                elements.push({
                    tag,
                    text,
                    id: el.id || '',
                    className: el.className || '',
                    href: (tag === 'a' && el.href) ? el.href : '',
                    role: el.getAttribute('role') || '',
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height
                });
            });
            return elements;
        }
        """
        return await self.execute_script(script)
    
    async def wait_for_selector(self, selector: str, timeout: int = 5000) -> None:
        """Wait for element to appear"""
        await self.page.wait_for_selector(selector, timeout=timeout)
    
    async def close(self) -> None:
        """Close browser and cleanup"""
        await self.page.close()
        await self.context.close()
        await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser closed")