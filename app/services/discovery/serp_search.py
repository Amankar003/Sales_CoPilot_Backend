"""
serp_search.py - DuckDuckGo search integration for discovering businesses.
"""

import time
from typing import List, Dict, Any
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def search_businesses_ddg(
    sector: str,
    location: str,
    max_runtime_seconds: int = 120,
) -> List[Dict[str, Any]]:
    """
    Search for businesses using DuckDuckGo.
    Returns a list of search results with basic business info.
    """
    try:
        from duckduckgo_search import DDGS

        query = f"{sector} in {location} India contact details"
        logger.info(f"DuckDuckGo search: '{query}'")

        results = []
        start_time = time.time()
        
        with DDGS() as ddgs:
            # Fetch a large technical cap of results
            search_iterator = ddgs.text(query, max_results=100)
            
            for result in search_iterator:
                if time.time() - start_time > max_runtime_seconds:
                    logger.info("DDG search stopped due to max runtime.")
                    break
                    
                business_info = {
                    "name": result.get("title", "Unknown"),
                    "description": result.get("body", ""),
                    "website": result.get("href", ""),
                    "source": "duckduckgo",
                }
                results.append(business_info)

        logger.info(f"DuckDuckGo returned {len(results)} results")
        return results

    except ImportError:
        logger.warning("duckduckgo-search not installed, skipping search")
        return []
    except Exception as e:
        logger.error(f"DuckDuckGo search error: {e}")
        return []


async def search_business_website(business_name: str, location: str) -> str | None:
    """Search for a specific business's website."""
    try:
        from duckduckgo_search import DDGS

        query = f"{business_name} {location} official website"
        logger.info(f"Searching website for: {business_name}")

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))

        for result in results:
            href = result.get("href", "")
            # Filter out social media and directory sites
            skip_domains = [
                "facebook.com", "instagram.com", "twitter.com",
                "linkedin.com", "youtube.com", "justdial.com",
                "sulekha.com", "indiamart.com", "yellowpages",
            ]
            if href and not any(d in href.lower() for d in skip_domains):
                return href

        return None
    except Exception as e:
        logger.error(f"Website search error for {business_name}: {e}")
        return None
