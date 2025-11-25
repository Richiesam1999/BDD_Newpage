"""
DOM Analyzer - Analyzes HTML structure and extracts semantic information
"""
import logging
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class DOMAnalyzer:
    """Analyzes DOM structure and extracts meaningful information"""
    
    def analyze(self, html_content: str, url: str) -> Dict[str, Any]:
        """
        Analyze HTML content and extract structural information
        
        Returns:
            Dictionary with DOM structure information
        """
        soup = BeautifulSoup(html_content, 'lxml')
        
        return {
            'url': url,
            'domain': urlparse(url).netloc,
            'title': self._get_title(soup),
            'navigation': self._analyze_navigation(soup),
            'page_type': self._infer_page_type(soup, url),
            'main_content_areas': self._identify_main_areas(soup),
            'element_count': self._count_elements(soup)
        }
    
    def _get_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else ''
    
    def _analyze_navigation(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze navigation structure"""
        nav_elements = soup.find_all(['nav', '[role="navigation"]'])
        
        menus = []
        for nav in nav_elements:
            links = nav.find_all('a')
            menus.append({
                'link_count': len(links),
                'items': [link.get_text().strip() for link in links[:10]]  # First 10
            })
        
        return {
            'nav_count': len(nav_elements),
            'menus': menus
        }
    
    def _infer_page_type(self, soup: BeautifulSoup, url: str) -> str:
        """Infer the type of page (e-commerce, blog, corporate, etc.)"""
        indicators = {
            'ecommerce': ['product', 'cart', 'checkout', 'price', 'buy'],
            'blog': ['article', 'post', 'author', 'comment'],
            'corporate': ['about', 'contact', 'services', 'team'],
            'healthcare': ['patient', 'doctor', 'treatment', 'medical']
        }
        
        text = soup.get_text().lower()
        url_lower = url.lower()
        
        scores = {}
        for page_type, keywords in indicators.items():
            score = sum(1 for keyword in keywords if keyword in text or keyword in url_lower)
            scores[page_type] = score
        
        max_type = max(scores, key=scores.get)
        return max_type if scores[max_type] > 0 else 'general'
    
    def _identify_main_areas(self, soup: BeautifulSoup) -> List[str]:
        """Identify main content areas"""
        areas = []
        
        # Check for header
        if soup.find('header'):
            areas.append('header')
        
        # Check for main content
        if soup.find('main') or soup.find('[role="main"]'):
            areas.append('main_content')
        
        # Check for sidebar
        if soup.find('aside') or soup.find('.sidebar'):
            areas.append('sidebar')
        
        # Check for footer
        if soup.find('footer'):
            areas.append('footer')
        
        return areas
    
    def _count_elements(self, soup: BeautifulSoup) -> Dict[str, int]:
        """Count various element types"""
        return {
            'links': len(soup.find_all('a')),
            'buttons': len(soup.find_all('button')),
            'forms': len(soup.find_all('form')),
            'images': len(soup.find_all('img'))
        }