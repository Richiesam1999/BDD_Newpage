"""
Element Detector - HOVER-FOCUSED VERSION
Detects elements that reveal dropdowns/menus on HOVER (not static links)
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from config import config

logger = logging.getLogger(__name__)


@dataclass
class ElementInfo:
    """Information about a detected element"""
    tag: str
    text: str
    role: str
    xpath: str
    attributes: Dict[str, str]
    location: Dict[str, float]
    
    def get_description(self) -> str:
        """Generate human-readable description"""
        if self.text:
            return f'"{self.text}"'
        elif self.attributes.get('aria-label'):
            return f'"{self.attributes["aria-label"]}"'
        else:
            return f'{self.role} element'


@dataclass
class MenuStructure:
    """Detailed structure of revealed menu/dropdown"""
    sections: List[Dict[str, Any]]
    all_links: List[str]
    menu_type: str
    layout: str


@dataclass
class Interaction:
    """Represents a detected interaction"""
    trigger_element: ElementInfo
    action_type: str
    interaction_method: str
    revealed_elements: List[ElementInfo]
    menu_structure: Optional[MenuStructure]
    url_before: str
    url_after: Optional[str]
    popup_appeared: bool
    popup_info: Optional[Dict[str, Any]] = None
    visual_changes: Optional[Dict[str, Any]] = None


class ElementDetector:
    """Detects HOVER-TRIGGERED menus and dropdowns"""
    
    def __init__(self, browser_automation):
        self.browser = browser_automation
        self.page = browser_automation.page
    
    async def find_hoverable_elements(self) -> List[ElementInfo]:
        """
        Find elements that TRIGGER dropdowns on hover
        NOT static links, but MENU TRIGGERS
        """
        logger.info("Detecting hover-triggered menu elements...")
        
        candidates = []
        
        try:
            # Strategy 1: Find elements with aria-haspopup or aria-expanded
            aria_triggers = await self._find_aria_menu_triggers()
            candidates.extend(aria_triggers)
            
            # Strategy 2: Find top-level nav items (not their children)
            nav_triggers = await self._find_nav_menu_triggers()
            candidates.extend(nav_triggers)
            
            # Strategy 3: Find elements with dropdown CSS classes
            css_triggers = await self._find_css_dropdown_triggers()
            candidates.extend(css_triggers)
            
            # Remove duplicates
            unique_elements = self._deduplicate_elements(candidates)
            
            logger.info(f"Found {len(unique_elements)} hover menu triggers")
            return unique_elements[:config.MAX_HOVER_ELEMENTS]
            
        except Exception as e:
            logger.error(f"Error finding hoverable elements: {str(e)}")
            return []
    
    async def _find_aria_menu_triggers(self) -> List[ElementInfo]:
        """Find elements with aria-haspopup or aria-expanded attributes"""
        script = """
        () => {
            const elements = [];
            const seen = new Set();
            
            // Find elements that TRIGGER menus (not the menu items themselves)
            const triggers = document.querySelectorAll('[aria-haspopup="true"], [aria-expanded]');
            
            triggers.forEach(el => {
                const rect = el.getBoundingClientRect();
                const text = el.textContent?.trim() || '';
                
                // Only top-level triggers (not nested menu items)
                if (rect.width > 0 && rect.height > 0 && 
                    text.length > 0 && text.length < 50 &&
                    !seen.has(text)) {
                    
                    seen.add(text);
                    
                    elements.push({
                        tag: el.tagName.toLowerCase(),
                        text: text,
                        role: el.getAttribute('role') || 'button',
                        xpath: getXPath(el),
                        attributes: {
                            id: el.id || '',
                            class: el.className || '',
                            'aria-label': el.getAttribute('aria-label') || '',
                            'aria-haspopup': el.getAttribute('aria-haspopup') || '',
                            'aria-expanded': el.getAttribute('aria-expanded') || ''
                        },
                        location: {
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height
                        }
                    });
                }
            });
            
            function getXPath(element) {
                if (element.id) return `//*[@id="${element.id}"]`;
                if (element === document.body) return '/html/body';
                
                let ix = 0;
                const siblings = element.parentNode?.childNodes || [];
                for (let i = 0; i < siblings.length; i++) {
                    const sibling = siblings[i];
                    if (sibling === element) {
                        return getXPath(element.parentNode) + '/' + 
                               element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                    }
                    if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                        ix++;
                    }
                }
            }
            
            return elements;
        }
        """
        
        try:
            raw_elements = await self.browser.execute_script(script)
            elements = [ElementInfo(**el) for el in raw_elements] if raw_elements else []
            logger.info(f"Found {len(elements)} ARIA menu triggers")
            return elements
        except Exception as e:
            logger.warning(f"Error finding ARIA triggers: {str(e)}")
            return []
    
    async def _find_nav_menu_triggers(self) -> List[ElementInfo]:
        """
        Find TOP-LEVEL navigation items that trigger dropdowns
        NOT their child links
        """
        script = """
        () => {
            const elements = [];
            const seen = new Set();
            
            // Find navigation containers
            const navs = document.querySelectorAll('nav, [role="navigation"], header nav');
            
            navs.forEach(nav => {
                // Get DIRECT children only (top-level items)
                const topLevelItems = nav.querySelectorAll(':scope > ul > li, :scope > div > a, :scope > div > button');
                
                topLevelItems.forEach(item => {
                    // Check if this item has children (submenu indicator)
                    const hasSubmenu = item.querySelector('ul, [role="menu"], .dropdown-menu, .submenu');
                    
                    if (hasSubmenu) {
                        // This is a menu trigger!
                        const trigger = item.querySelector('a, button') || item;
                        const rect = trigger.getBoundingClientRect();
                        const text = trigger.textContent?.trim() || '';
                        
                        if (rect.width > 0 && rect.height > 0 && 
                            text.length > 0 && text.length < 50 &&
                            !seen.has(text)) {
                            
                            seen.add(text);
                            
                            elements.push({
                                tag: trigger.tagName.toLowerCase(),
                                text: text,
                                role: 'menuitem',
                                xpath: getXPath(trigger),
                                attributes: {
                                    id: trigger.id || '',
                                    class: trigger.className || '',
                                    'aria-label': trigger.getAttribute('aria-label') || '',
                                    href: trigger.href || ''
                                },
                                location: {
                                    x: rect.x,
                                    y: rect.y,
                                    width: rect.width,
                                    height: rect.height
                                }
                            });
                        }
                    }
                });
            });
            
            function getXPath(element) {
                if (element.id) return `//*[@id="${element.id}"]`;
                if (element === document.body) return '/html/body';
                
                let ix = 0;
                const siblings = element.parentNode?.childNodes || [];
                for (let i = 0; i < siblings.length; i++) {
                    const sibling = siblings[i];
                    if (sibling === element) {
                        return getXPath(element.parentNode) + '/' + 
                               element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                    }
                    if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                        ix++;
                    }
                }
            }
            
            return elements;
        }
        """
        
        try:
            raw_elements = await self.browser.execute_script(script)
            elements = [ElementInfo(**el) for el in raw_elements] if raw_elements else []
            logger.info(f"Found {len(elements)} navigation menu triggers")
            return elements
        except Exception as e:
            logger.warning(f"Error finding nav triggers: {str(e)}")
            return []
    
    async def _find_css_dropdown_triggers(self) -> List[ElementInfo]:
        """Find elements with dropdown-related CSS classes"""
        script = """
        () => {
            const elements = [];
            const seen = new Set();
            
            // Common dropdown trigger class patterns
            const patterns = [
                '[class*="dropdown"]',
                '[class*="has-submenu"]',
                '[class*="has-dropdown"]',
                '[class*="menu-item-has-children"]'
            ];
            
            patterns.forEach(pattern => {
                document.querySelectorAll(pattern).forEach(el => {
                    // Get the clickable/hoverable part
                    const trigger = el.querySelector('a, button, span') || el;
                    const rect = trigger.getBoundingClientRect();
                    const text = trigger.textContent?.trim() || '';
                    
                    if (rect.width > 0 && rect.height > 0 && 
                        text.length > 0 && text.length < 50 &&
                        !seen.has(text)) {
                        
                        seen.add(text);
                        
                        elements.push({
                            tag: trigger.tagName.toLowerCase(),
                            text: text,
                            role: 'menuitem',
                            xpath: getXPath(trigger),
                            attributes: {
                                id: trigger.id || '',
                                class: trigger.className || '',
                                'aria-label': trigger.getAttribute('aria-label') || ''
                            },
                            location: {
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height
                            }
                        });
                    }
                });
            });
            
            function getXPath(element) {
                if (element.id) return `//*[@id="${element.id}"]`;
                if (element === document.body) return '/html/body';
                
                let ix = 0;
                const siblings = element.parentNode?.childNodes || [];
                for (let i = 0; i < siblings.length; i++) {
                    const sibling = siblings[i];
                    if (sibling === element) {
                        return getXPath(element.parentNode) + '/' + 
                               element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                    }
                    if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                        ix++;
                    }
                }
            }
            
            return elements;
        }
        """
        
        try:
            raw_elements = await self.browser.execute_script(script)
            elements = [ElementInfo(**el) for el in raw_elements] if raw_elements else []
            logger.info(f"Found {len(elements)} CSS dropdown triggers")
            return elements
        except Exception as e:
            logger.warning(f"Error finding CSS triggers: {str(e)}")
            return []
    
    def _deduplicate_elements(self, elements: List[ElementInfo]) -> List[ElementInfo]:
        """Remove duplicate elements based on text"""
        seen_texts = set()
        unique = []
        
        for el in elements:
            if el.text and el.text not in seen_texts:
                seen_texts.add(el.text)
                unique.append(el)
        
        return unique
    
    async def simulate_hover_interaction(self, element: ElementInfo) -> Optional[Interaction]:
        """
        Test if hovering reveals a dropdown menu
        """
        try:
            logger.info(f"Testing HOVER on: {element.get_description()}")
            
            url_before = await self.browser.get_current_url()
            
            # Get initial visible menu count
            menus_before = await self._count_visible_menus()
            
            # Hover over element
            locator = self.page.locator(f"xpath={element.xpath}").first
            await locator.scroll_into_view_if_needed()
            await locator.hover()
            await asyncio.sleep(1.0)  # Wait for dropdown animation
            
            # Check if new menus appeared
            menus_after = await self._count_visible_menus()
            
            if menus_after > menus_before:
                logger.info(f"✓ DROPDOWN APPEARED on hover over {element.get_description()}")
                
                # Extract menu structure
                menu_structure = await self._extract_revealed_menu_structure()
                
                # Get clickable links
                clickable_links = []
                if menu_structure and menu_structure.get('links'):
                    clickable_links = await self._extract_clickable_links(menu_structure['links'])
                
                return Interaction(
                    trigger_element=element,
                    action_type='hover',
                    interaction_method='hover-menu',
                    revealed_elements=[],
                    menu_structure=MenuStructure(
                        sections=menu_structure.get('sections', []) if menu_structure else [],
                        all_links=menu_structure.get('all_links', []) if menu_structure else [],
                        menu_type=menu_structure.get('menu_type', 'dropdown') if menu_structure else 'dropdown',
                        layout='single-column'
                    ) if menu_structure else None,
                    url_before=url_before,
                    url_after=None,
                    popup_appeared=False,
                    visual_changes={'clickable_links': clickable_links} if clickable_links else None
                )
            else:
                logger.debug(f"✗ No dropdown on hover: {element.get_description()}")
                return None
            
        except Exception as e:
            logger.warning(f"Failed to test hover: {str(e)}")
            return None
    
    async def _count_visible_menus(self) -> int:
        """Count currently visible dropdown menus"""
        script = """
        () => {
            let count = 0;
            const menuSelectors = [
                '[role="menu"]',
                '.dropdown-menu',
                '.submenu',
                'ul[class*="sub"]',
                '[class*="dropdown"][style*="display"][style*="block"]'
            ];
            
            menuSelectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(menu => {
                    const styles = window.getComputedStyle(menu);
                    const rect = menu.getBoundingClientRect();
                    
                    if (styles.display !== 'none' && 
                        styles.visibility !== 'hidden' &&
                        styles.opacity !== '0' &&
                        rect.width > 20 && rect.height > 20) {
                        count++;
                    }
                });
            });
            
            return count;
        }
        """
        return await self.browser.execute_script(script)
    
    async def _extract_revealed_menu_structure(self) -> Optional[Dict[str, Any]]:
        """Extract links from the revealed dropdown"""
        script = """
        () => {
            const menuSelectors = [
                '[role="menu"]',
                '.dropdown-menu',
                '.submenu',
                'ul[class*="sub"]'
            ];
            
            for (const selector of menuSelectors) {
                const menus = document.querySelectorAll(selector);
                
                for (const menu of menus) {
                    const styles = window.getComputedStyle(menu);
                    const rect = menu.getBoundingClientRect();
                    
                    if (styles.display !== 'none' && 
                        styles.visibility !== 'hidden' &&
                        rect.width > 20 && rect.height > 20) {
                        
                        const links = [];
                        menu.querySelectorAll('a').forEach(link => {
                            const linkText = link.textContent?.trim() || '';
                            const linkHref = link.href || '';
                            
                            if (linkText && linkHref) {
                                links.push({
                                    text: linkText,
                                    href: linkHref
                                });
                            }
                        });
                        
                        if (links.length > 0) {
                            return {
                                menu_type: 'dropdown',
                                sections: [],
                                all_links: links.map(l => l.text),
                                links: links
                            };
                        }
                    }
                }
            }
            
            return null;
        }
        """
        
        return await self.browser.execute_script(script)
    
    async def _extract_clickable_links(self, links: List[Dict]) -> List[Dict[str, str]]:
        """Process extracted links"""
        clickable = []
        seen = set()
        
        for link in links[:10]:
            text = link.get('text', '').strip()
            href = link.get('href', '')
            
            if text and href and href not in seen:
                seen.add(href)
                clickable.append({'text': text, 'target_url': href})
        
        logger.info(f"Extracted {len(clickable)} clickable links from dropdown")
        return clickable
    
    async def detect_popup_triggers(self) -> List[ElementInfo]:
        """Find button/link triggers for popups/modals"""
        logger.info("Detecting popup triggers...")
        
        script = """
        () => {
            const elements = [];
            const selectors = [
                'button[data-toggle="modal"]',
                '[data-target*="modal"]',
                'a[href*="#modal"]',
                '.modal-trigger',
                '[onclick*="modal"]'
            ];
            
            selectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(el => {
                    const rect = el.getBoundingClientRect();
                    const text = el.textContent?.trim() || '';
                    
                    if (rect.width > 0 && rect.height > 0 && text) {
                        elements.push({
                            tag: el.tagName.toLowerCase(),
                            text: text.substring(0, 100),
                            role: 'button',
                            xpath: getXPath(el),
                            attributes: {
                                id: el.id || '',
                                class: el.className || ''
                            },
                            location: {
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height
                            }
                        });
                    }
                });
            });
            
            function getXPath(element) {
                if (element.id) return `//*[@id="${element.id}"]`;
                let ix = 0;
                const siblings = element.parentNode?.childNodes || [];
                for (let i = 0; i < siblings.length; i++) {
                    if (siblings[i] === element) {
                        return getXPath(element.parentNode) + '/' + 
                               element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                    }
                    if (siblings[i].nodeType === 1 && siblings[i].tagName === element.tagName) {
                        ix++;
                    }
                }
            }
            
            return elements;
        }
        """
        
        try:
            raw_elements = await self.browser.execute_script(script)
            elements = [ElementInfo(**el) for el in raw_elements] if raw_elements else []
            logger.info(f"Found {len(elements)} popup triggers")
            return elements[:config.MAX_POPUP_TRIGGERS]
        except Exception as e:
            logger.error(f"Error detecting popups: {str(e)}")
            return []
    
    async def simulate_popup_interaction(self, element: ElementInfo) -> Optional[Interaction]:
        """Test popup trigger (keep existing implementation)"""
        # ... existing popup code ...
        return None