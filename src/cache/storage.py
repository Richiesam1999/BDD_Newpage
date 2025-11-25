"""
Cache Storage - SQLite-based caching for DOM analysis results
"""
import aiosqlite
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path
from config import config

logger = logging.getLogger(__name__)


class DOMCache:
    """SQLite-based cache for storing analysis results"""
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or config.CACHE_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Create database schema if not exists"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    url TEXT PRIMARY KEY,
                    interactions TEXT,
                    scenarios TEXT,
                    feature_content TEXT,
                    created_at TEXT,
                    expires_at TEXT
                )
            """)
            await db.commit()
    
    async def store_analysis(
        self, 
        url: str, 
        interactions: List[Any], 
        scenarios: List[Any],
        feature_content: str = None
    ) -> None:
        """Store analysis results in cache"""
        await self.initialize()
        
        created_at = datetime.now().isoformat()
        expires_at = (datetime.now() + timedelta(hours=config.CACHE_EXPIRY_HOURS)).isoformat()
        
        # Serialize interactions and scenarios
        interactions_json = json.dumps([self._serialize_interaction(i) for i in interactions])
        scenarios_json = json.dumps([self._serialize_scenario(s) for s in scenarios])
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO cache (url, interactions, scenarios, feature_content, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (url, interactions_json, scenarios_json, feature_content, created_at, expires_at))
            await db.commit()
        
        logger.info(f"Cached analysis for {url}")
    
    async def get_cached_analysis(self, url: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached analysis if available and not expired"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM cache WHERE url = ?", (url,)
            ) as cursor:
                row = await cursor.fetchone()
                
                if not row:
                    return None
                
                # Check expiration
                expires_at = datetime.fromisoformat(row['expires_at'])
                if datetime.now() > expires_at:
                    logger.info(f"Cache expired for {url}")
                    await self.invalidate_cache(url)
                    return None
                
                logger.info(f"Cache hit for {url}")
                return {
                    'url': row['url'],
                    'interactions': json.loads(row['interactions']),
                    'scenarios': json.loads(row['scenarios']),
                    'feature_content': row['feature_content'],
                    'created_at': row['created_at']
                }
    
    async def invalidate_cache(self, url: str) -> None:
        """Remove cached entry"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM cache WHERE url = ?", (url,))
            await db.commit()
    
    async def clear_all(self) -> None:
        """Clear entire cache"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM cache")
            await db.commit()
        logger.info("Cache cleared")
    
    def _serialize_interaction(self, interaction: Any) -> Dict:
        """Convert Interaction object to dict"""
        return {
            'action_type': interaction.action_type,
            'trigger_element': {
                'text': interaction.trigger_element.text,
                'tag': interaction.trigger_element.tag,
                'role': interaction.trigger_element.role
            },
            'popup_appeared': interaction.popup_appeared
        }
    
    def _serialize_scenario(self, scenario: Any) -> Dict:
        """Convert TestScenario object to dict"""
        return {
            'feature_name': scenario.feature_name,
            'scenario_name': scenario.scenario_name,
            'steps': scenario.steps,
            'scenario_type': scenario.scenario_type
        }