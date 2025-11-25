
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
    """Detects HOVER-TRIGGERED menus, dropdowns, and popup triggers"""
    
    def __init__(self, browser_automation):
        self.browser = browser_automation
        self.page = browser_automation.page

    async def detect_initial_popup(self, url: str) -> Optional[Interaction]:
        """Detect a popup/modal that appears automatically on page load.

        This runs a single popup scan without any user action, useful for
        cookie banners or acquisition overlays that appear immediately.
        """
        popup_info = await self._detect_popup()
        if not popup_info:
            return None

        # Heuristic: if the detected "popup" contains many buttons/links, it is
        # likely a global navigation panel (e.g., mega menu) rather than a
        # true modal dialog/banner. We skip such cases here to avoid
        # misclassifying the primary nav as a popup on page load.
        try:
            buttons = popup_info.get("buttons") or []
            if len(buttons) >= 10:
                logger.info(
                    "Initial popup candidate has %d buttons; treating it as layout/nav, not popup",
                    len(buttons),
                )
                return None
        except Exception:
            # If anything goes wrong with this heuristic, fall back to
            # original behavior to avoid hiding real popups.
            pass

        logger.info("✓ Initial popup detected on page load")

        trigger_element = ElementInfo(
            tag='body',
            text='page load popup',
            role='load',
            xpath='//body',
            attributes={},
            location={}
        )

        return Interaction(
            trigger_element=trigger_element,
            action_type='load',
            interaction_method='auto-popup',
            revealed_elements=[],
            menu_structure=None,
            url_before=url,
            url_after=None,
            popup_appeared=True,
            popup_info=popup_info,
            visual_changes=None,
        )
    
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
            nav_triggers_strict = await self._find_nav_menu_triggers()
            candidates.extend(nav_triggers_strict)

            # Strategy 2b: Loose nav scanning for custom navs (e.g., Apple)
            nav_triggers_loose = await self._find_nav_menu_triggers_loose()
            candidates.extend(nav_triggers_loose)
            
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
        """Strict nav trigger detection based on submenu structure.

        This is the original, conservative implementation that worked well for
        sites like Tivdak and Nike. It looks for top-level <li> items that have
        nested <ul>/<role="menu">/.dropdown-menu/.submenu children.
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
            logger.info(f"Found {len(elements)} strict navigation menu triggers")
            return elements
        except Exception as e:
            logger.warning(f"Error finding nav triggers: {str(e)}")
            return []

    async def _find_nav_menu_triggers_loose(self) -> List[ElementInfo]:
        """Loose nav trigger detection for custom navs (e.g., Apple globalnav).

        This is more permissive and does not require visible submenus. It
        simply finds visible, labeled nav items near the top of the page and
        lets simulate_hover_interaction + diffing decide if they actually
        produce dropdown content.
        """
        script = """
        () => {
            const elements = [];
            const seen = new Set();

            // Find navigation containers (global nav, header nav, ARIA navigation)
            const navs = document.querySelectorAll('nav, [role="navigation"], header nav');

            navs.forEach(nav => {
                // Consider interactive items (a/button/role=button) inside the nav
                const triggers = nav.querySelectorAll('a, button, [role="button"]');

                triggers.forEach(trigger => {
                    const rect = trigger.getBoundingClientRect();
                    const styles = window.getComputedStyle(trigger);
                    const text = (trigger.textContent || '').trim();

                    // Visible, within top portion of page, and with a short label
                    if (rect.width <= 0 || rect.height <= 0) return;
                    if (styles.display === 'none' || styles.visibility === 'hidden') return;

                    // Only consider items in the top ~200px to avoid footer navs
                    if (rect.top > 200) return;

                    if (!text || text.length > 50) return;

                    const key = text.toLowerCase();
                    if (seen.has(key)) return;
                    seen.add(key);

                    elements.push({
                        tag: trigger.tagName.toLowerCase(),
                        text: text,
                        role: trigger.getAttribute('role') || 'menuitem',
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
            logger.info(f"Found {len(elements)} loose navigation menu triggers")
            return elements
        except Exception as e:
            logger.warning(f"Error finding loose nav triggers: {str(e)}")
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
        """Test if hovering reveals a dropdown menu or new navigation links.

        Primary path:
        - Use menu containers (role="menu", .dropdown-menu, etc.) and a
          before/after content signature to detect dropdowns.

        Fallback path (for highly custom navs like apple.com):
        - Diff visible elements before/after hover and extract *new* anchor
          links that appear near the trigger in the header area. These are
          treated as dropdown navigation options even if there is no explicit
          menu container.
        """
        try:
            logger.info(f"Testing HOVER on: {element.get_description()}")

            url_before = await self.browser.get_current_url()

            # Snapshot visible elements before hover for diff-based fallback
            visible_before = await self.browser.get_visible_elements()

            # Get initial menu state (count + content signature)
            menu_state_before = await self._get_menu_state()

            # Hover over element
            locator = self.page.locator(f"xpath={element.xpath}").first
            await locator.scroll_into_view_if_needed()

            # Use a smaller, explicit timeout for hover so we don't block for the
            # full page default (e.g. 30000ms) when an XPath is stale/invalid.
            try:
                await locator.hover(timeout=5000)
            except Exception as hover_err:
                logger.warning(f"Hover action failed for {element.get_description()}: {hover_err}")
                return None

            await asyncio.sleep(1.0)  # Wait for dropdown animation

            # Check menu state after hover
            menu_state_after = await self._get_menu_state()

            menus_before = int(menu_state_before.get("count", 0) or 0)
            menus_after = int(menu_state_after.get("count", 0) or 0)
            signature_before = menu_state_before.get("signature", "") or ""
            signature_after = menu_state_after.get("signature", "") or ""

            dropdown_detected = False

            # 1) New menu became visible
            if menus_after > menus_before:
                dropdown_detected = True
            # 2) Same number of menus, but visible menu content changed
            elif menus_after >= 1 and signature_after != signature_before:
                dropdown_detected = True

            if dropdown_detected:
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

            # Fallback: diff visible elements to detect new nav links even when
            # there is no explicit menu container.
            visible_after = await self.browser.get_visible_elements()
            fallback_links = self._extract_new_nav_links(visible_before, visible_after, element)

            if fallback_links:
                logger.info(
                    f"✓ Detected {len(fallback_links)} navigation link(s) via diff after hover over {element.get_description()}"
                )
                return Interaction(
                    trigger_element=element,
                    action_type='hover',
                    interaction_method='hover-nav-diff',
                    revealed_elements=[],
                    menu_structure=None,
                    url_before=url_before,
                    url_after=None,
                    popup_appeared=False,
                    visual_changes={'clickable_links': fallback_links},
                )

            logger.debug(f"✗ No dropdown or new nav links on hover: {element.get_description()}")
            return None

        except Exception as e:
            logger.warning(f"Failed to test hover: {str(e)}")
            return None

    async def _get_menu_state(self) -> Dict[str, Any]:
        """Return current dropdown/menu state (count + simple content signature).

        The content signature lets us detect when a shared dropdown container
        changes its contents even if the number of visible menus stays the same.
        """
        script = """
        () => {
            const menuSelectors = [
                '[role="menu"]',
                '.dropdown-menu',
                '.submenu',
                'ul[class*="sub"]',
                '[class*="dropdown"][style*="display"][style*="block"]'
            ];

            const visibleMenus = [];

            menuSelectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(menu => {
                    const styles = window.getComputedStyle(menu);
                    const rect = menu.getBoundingClientRect();

                    if (styles.display !== 'none' &&
                        styles.visibility !== 'hidden' &&
                        styles.opacity !== '0' &&
                        rect.width > 20 && rect.height > 20) {
                        const text = (menu.innerText || '').trim().substring(0, 300);
                        visibleMenus.push({
                            id: menu.id || '',
                            className: menu.className || '',
                            text,
                        });
                    }
                });
            });

            // Build a lightweight, order-stable signature of visible menu content
            const signature = visibleMenus
                .map(m => `${m.id}|${m.className}|${m.text}`)
                .join('||');

            return {
                count: visibleMenus.length,
                signature,
            };
        }
        """

        try:
            state = await self.browser.execute_script(script)
            return state or {"count": 0, "signature": ""}
        except Exception as e:
            logger.warning(f"Failed to read menu state: {e}")
            return {"count": 0, "signature": ""}
    
    def _extract_new_nav_links(
        self,
        before: List[Dict[str, Any]],
        after: List[Dict[str, Any]],
        trigger_element: ElementInfo,
    ) -> List[Dict[str, str]]:
        """Extract newly visible navigation links near the trigger.

        This is a generic fallback that does not rely on specific menu
        containers. It looks for new <a> elements that:
        - Have a non-empty href and text.
        - Were not present before the hover.
        - Appear within a vertical band near the trigger (header area).
        """
        before_keys = set()
        for el in before:
            href = (el.get('href') or '').strip()
            text = (el.get('text') or '').strip()
            if href and text:
                before_keys.add((href, text))

        trigger_y = trigger_element.location.get('y', 0.0) or 0.0
        max_delta_y = 500  # pixels below trigger to still consider part of dropdown

        new_links: List[Dict[str, str]] = []
        seen_hrefs = set()

        for el in after:
            href = (el.get('href') or '').strip()
            text = (el.get('text') or '').strip()
            if not href or not text:
                continue

            key = (href, text)
            if key in before_keys:
                continue

            y = float(el.get('y', 0.0) or 0.0)
            # Only consider links that appear around/just below the trigger in the
            # upper portion of the page (to avoid footer content).
            if y < 0:
                continue
            if y > trigger_y + max_delta_y:
                continue

            if href in seen_hrefs:
                continue
            seen_hrefs.add(href)
            new_links.append({'text': text, 'target_url': href})

        if new_links:
            logger.info(f"Extracted {len(new_links)} new navigation link(s) from diff")
        return new_links

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
        
        # Strategy 1: Classic modal-related attributes/classes
        script = """
        () => {
            const elements = [];
            const selectors = [
                'button[data-toggle="modal"]',
                '[data-target*="modal"]',
                'a[href*="#modal"]',
                '.modal-trigger',
                '[onclick*="modal"]',
                // Generic CTA buttons/links that often trigger popups
                'a[data-modal]',
                'button[data-modal]',
                'a[role="button"]',
                'button[role="button"]'
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
                if (element.id) return `//*[@id=\"${element.id}\"]`;
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
        
        candidates: List[ElementInfo] = []
        try:
            raw_elements = await self.browser.execute_script(script)
            if raw_elements:
                candidates.extend(ElementInfo(**el) for el in raw_elements)
        except Exception as e:
            logger.error(f"Error detecting classic popup triggers: {str(e)}")

        # Strategy 2: External-link based triggers (e.g., "You are leaving" popups)
        try:
            external_triggers = await self._find_external_link_triggers()
            candidates.extend(external_triggers)
        except Exception as e:
            logger.warning(f"Error detecting external-link popup triggers: {e}")

        # Deduplicate by (text, xpath)
        unique: List[ElementInfo] = []
        seen_keys = set()
        for el in candidates:
            key = (el.text, el.xpath)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            unique.append(el)

        logger.info(f"Found {len(unique)} popup triggers (combined strategies)")
        return unique[:config.MAX_POPUP_TRIGGERS]

    async def _find_external_link_triggers(self) -> List[ElementInfo]:
        """Find visible external links likely protected by a "leaving site" popup.

        This is especially useful for pharma/regulated sites like Tivdak where
        external CTAs (e.g., "Learn More") often trigger a confirmation modal
        before navigating to an external domain.
        """
        script = """
        () => {
            const elements = [];
            const seen = new Set();
            const currentHost = window.location.hostname.replace(/^www\./, '');

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

            const anchors = document.querySelectorAll('a[href]');
            anchors.forEach(a => {
                const rect = a.getBoundingClientRect();
                const styles = window.getComputedStyle(a);
                const text = (a.textContent || '').trim();

                if (rect.width <= 0 || rect.height <= 0) return;
                if (styles.display === 'none' || styles.visibility === 'hidden') return;
                if (!text) return;

                let url;
                try {{
                    url = new URL(a.href, window.location.href);
                }} catch (e) {{
                    return;
                }}
                const host = url.hostname.replace(/^www\./, '');
                if (host === currentHost) return; // not external

                // Avoid obviously unrelated links (e.g., footer social icons) by y-position.
                // Use a generous threshold (95% of viewport height) so mid-page CTAs
                // like Tivdak's "Learn More" button are still included.
                if (rect.top > window.innerHeight * 0.95) return;

                const key = `${text.toLowerCase()}|${url.href}`;
                if (seen.has(key)) return;
                seen.add(key);

                elements.push({
                    tag: 'a',
                    text: text.substring(0, 100),
                    role: 'link',
                    xpath: getXPath(a),
                    attributes: {
                        id: a.id || '',
                        class: a.className || '',
                        href: a.href || ''
                    },
                    location: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    }
                });
            });

            return elements;
        }
        """

        raw_elements = await self.browser.execute_script(script)
        return [ElementInfo(**el) for el in (raw_elements or [])]
    
    async def _detect_popup(self) -> Optional[Dict[str, Any]]:
        """Detect a visible popup/modal/overlay if present.

        We look for common dialog/modal patterns and return the first visible
        one along with its title and buttons (including hrefs for <a> tags).
        """
        script = """
        () => {
            const modalSelectors = [
                '[role="dialog"]',
                '[role="alertdialog"]',
                'dialog',
                '.modal',
                '.popup',
                '.dialog',
                '[class*="modal"]',
                '[class*="popup"]',
                '[class*="dialog"]',
                '[data-modal]',
                '[data-testid*="modal"]'
            ];

            for (const selector of modalSelectors) {
                const modals = document.querySelectorAll(selector);
                for (const modal of modals) {
                    const styles = window.getComputedStyle(modal);
                    const rect = modal.getBoundingClientRect();

                    if (styles.display === 'none' ||
                        styles.visibility === 'hidden' ||
                        rect.width <= 0 || rect.height <= 0) {
                        continue;
                    }

                    const opacity = parseFloat(styles.opacity || '1');
                    if (opacity === 0) continue;

                    const titleEl = modal.querySelector('h1, h2, h3, [role="heading"]');
                    const title = titleEl ? (titleEl.innerText || '').trim() : '';

                    const buttons = [];
                    const btnNodes = modal.querySelectorAll('button, [role="button"], a');
                    btnNodes.forEach(btn => {
                        const text = (btn.innerText || '').trim();
                        if (!text) return;
                        const tag = btn.tagName.toLowerCase();
                        const href = tag === 'a' ? (btn.href || '') : '';
                        buttons.push({
                            text,
                            class: btn.className || '',
                            href
                        });
                    });

                    return {
                        title,
                        content: (modal.innerText || '').trim().substring(0, 200),
                        buttons,
                        selector
                    };
                }
            }

            return null;
        }
        """

        try:
            return await self.browser.execute_script(script)
        except Exception as e:
            logger.warning(f"Error detecting popup/modal: {e}")
            return None
    
    async def simulate_popup_interaction(self, element: ElementInfo) -> Optional[Interaction]:
        """Click a potential popup trigger and capture overlay-style popups.

        IMPORTANT classification rule (per requirements):
        - If clicking causes a **popup/overlay** and the URL **does NOT change**, we
          treat it as a popup.
        - If clicking causes navigation (URL change), we do **not** classify it as
          a popup interaction here; that's a normal page navigation.
        """
        try:
            logger.info(f"Testing POPUP trigger on: {element.get_description()}")

            url_before = await self.browser.get_current_url()

            locator = self.page.locator(f"xpath={element.xpath}").first
            await locator.scroll_into_view_if_needed()
            try:
                await locator.click(timeout=config.INTERACTION_TIMEOUT * 1000)
            except Exception as click_err:
                logger.warning(f"Click failed for {element.get_description()}: {click_err}")
                return None

            # Wait briefly for popup animations
            await asyncio.sleep(1.0)

            popup_info = await self._detect_popup()
            url_after = await self.browser.get_current_url()

            # Only treat as popup if an overlay appears **and** URL did not change
            if popup_info and url_after == url_before:
                logger.info(
                    f"✓ Overlay-style popup detected (no navigation) after clicking {element.get_description()}"
                )
                return Interaction(
                    trigger_element=element,
                    action_type='click',
                    interaction_method='click-popup',
                    revealed_elements=[],
                    menu_structure=None,
                    url_before=url_before,
                    url_after=None,
                    popup_appeared=True,
                    popup_info=popup_info,
                    visual_changes=None,
                )

            if popup_info and url_after != url_before:
                logger.info(
                    f"Popup/modal detected but URL changed after clicking {element.get_description()} - treating as navigation, not popup interaction"
                )

            logger.debug(f"✗ No qualifying popup detected after clicking: {element.get_description()}")
            return None

        except Exception as e:
            logger.warning(f"Failed to test popup on {element.get_description()}: {e}")
            return None

    async def find_advanced_popup_interactions(self) -> List[Interaction]:
        """Advanced popup detection by exploring CTA-like elements.

        This is opt-in (config.ENABLE_ADVANCED_POPUP_DETECTION) and is intended
        as a fallback for modern sites where classic popup trigger selectors
        miss JS-driven modals. It clicks a small set of mid-page CTAs and
        records any resulting popups.
        """
        interactions: List[Interaction] = []

        if not getattr(config, "ENABLE_ADVANCED_POPUP_DETECTION", False):
            return interactions

        # Find candidate CTAs in the page
        script = """
        () => {
            const elements = [];
            const seen = new Set();
            const viewportHeight = window.innerHeight || 0;

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

            const selectors = [
                'button',
                'a[role="button"]',
                'a.button',
                '.btn',
                '.cta',
                '.cta-button'
            ];

            document.querySelectorAll(selectors.join(',')).forEach(el => {
                const rect = el.getBoundingClientRect();
                const styles = window.getComputedStyle(el);
                const text = (el.textContent || '').trim();

                if (rect.width <= 0 || rect.height <= 0) return;
                if (styles.display === 'none' || styles.visibility === 'hidden') return;
                if (!text) return;

                // Avoid header nav and footer links: focus on mid-page CTAs
                if (rect.top < 80) return;
                if (rect.top > viewportHeight * 0.85) return;

                const key = `${text.toLowerCase()}|${rect.top}|${rect.left}`;
                if (seen.has(key)) return;
                seen.add(key);

                elements.push({
                    tag: el.tagName.toLowerCase(),
                    text: text.substring(0, 100),
                    role: el.getAttribute('role') || 'button',
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
            });

            return elements;
        }
        """

        try:
            raw_elements = await self.browser.execute_script(script)
        except Exception as e:
            logger.warning(f"Advanced popup: candidate scan failed: {e}")
            return interactions

        if not raw_elements:
            logger.info("Advanced popup: no CTA candidates found")
            return interactions

        candidates = [ElementInfo(**el) for el in raw_elements]

        # Limit number of candidates to avoid over-clicking
        for element in candidates[: min(len(candidates), config.MAX_POPUP_TRIGGERS)]:
            interaction = await self.simulate_popup_interaction(element)
            if interaction and interaction.popup_appeared:
                interactions.append(interaction)

        logger.info(f"Advanced popup: detected {len(interactions)} popup interaction(s)")
        return interactions

    async def find_advanced_hover_interactions(self) -> List[Interaction]:
        """Advanced hover detection for modern navs (opt-in, non-breaking).

        This uses a MutationObserver inside the page to watch for style/ARIA
        changes on <a> elements while we synthetically hover nav triggers.
        It is only meant to be used when primary strategies found no
        interactions, and is gated by config.ENABLE_ADVANCED_HOVER_DETECTION.
        """
        interactions: List[Interaction] = []

        if not getattr(config, "ENABLE_ADVANCED_HOVER_DETECTION", False):
            return interactions

        # Use loose nav triggers (top-of-page nav items) as candidates
        loose_triggers = await self._find_nav_menu_triggers_loose()
        if not loose_triggers:
            logger.info("Advanced hover: no loose nav triggers found")
            return interactions

        for element in loose_triggers:
            try:
                url_before = await self.browser.get_current_url()

                xpath_escaped = element.xpath.replace('"', '\"')
                script = f"""
                () => {{
                    function snapshot(els) {{
                        const out = [];
                        els.forEach(el => {{
                            if (!(el instanceof HTMLAnchorElement)) return;
                            const rect = el.getBoundingClientRect();
                            const styles = window.getComputedStyle(el);
                            out.push({{
                                href: el.href || '',
                                text: (el.textContent || '').trim(),
                                x: rect.x,
                                y: rect.y,
                                opacity: parseFloat(styles.opacity || '1'),
                                display: styles.display,
                                visibility: styles.visibility,
                                ariaHidden: el.getAttribute('aria-hidden') || ''
                            }});
                        }});
                        return out;
                    }}

                    const xpath = "{xpath_escaped}";
                    function getElementByXPath(path) {{
                        return document.evaluate(path, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    }}

                    const trigger = getElementByXPath(xpath);
                    if (!trigger) {{
                        return null;
                    }}

                    const allLinks = Array.from(document.querySelectorAll('a'));
                    const before = snapshot(allLinks);

                    return new Promise(resolve => {{
                        const changed = new Set();
                        const observer = new MutationObserver(muts => {{
                            muts.forEach(m => {{
                                const t = m.target;
                                if (!(t instanceof HTMLElement)) return;
                                if (t.tagName.toLowerCase() !== 'a') return;
                                changed.add(t);
                            }});
                        }});

                        observer.observe(document.body, {{
                            attributes: true,
                            childList: true,
                            subtree: true,
                            attributeFilter: ['class', 'style', 'aria-hidden']
                        }});

                        const ev = new MouseEvent('mouseover', {{
                            bubbles: true,
                            cancelable: true,
                            view: window
                        }});
                        trigger.dispatchEvent(ev);

                        setTimeout(() => {{
                            observer.disconnect();
                            const after = snapshot(Array.from(changed));
                            resolve({{ before, after }});
                        }}, 800);
                    }});
                }}
                """

                result = await self.browser.execute_script(script)
                if not result:
                    continue

                before = result.get("before") or []
                after = result.get("after") or []
                if not after:
                    continue

                before_keys = set(
                    ((b.get("href") or "").strip(), (b.get("text") or "").strip())
                    for b in before
                    if b.get("href") and b.get("text")
                )

                new_links: List[Dict[str, str]] = []
                seen_hrefs = set()

                for a in after:
                    href = (a.get("href") or "").strip()
                    text = (a.get("text") or "").strip()
                    if not href or not text:
                        continue

                    key = (href, text)
                    if key in before_keys:
                        # If it existed before but now appears fully visible and not aria-hidden,
                        # treat it as "revealed".
                        opacity = float(a.get("opacity", 1) or 1)
                        aria_hidden = (a.get("ariaHidden") or "").strip()
                        if opacity < 0.95 or aria_hidden:
                            continue

                    if href in seen_hrefs:
                        continue
                    seen_hrefs.add(href)
                    new_links.append({"text": text, "target_url": href})

                if not new_links:
                    continue

                logger.info(
                    f"Advanced hover: found {len(new_links)} link(s) for {element.get_description()}"
                )

                interactions.append(
                    Interaction(
                        trigger_element=element,
                        action_type="hover",
                        interaction_method="hover-advanced",
                        revealed_elements=[],
                        menu_structure=None,
                        url_before=url_before,
                        url_after=None,
                        popup_appeared=False,
                        visual_changes={"clickable_links": new_links},
                    )
                )

            except Exception as e:
                logger.warning(
                    f"Advanced hover failed for {element.get_description()}: {e}"
                )

        return interactions
