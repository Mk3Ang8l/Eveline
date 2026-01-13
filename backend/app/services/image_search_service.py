"""
Image Search Service - Pure Node.js Playwright Implementation
"""

import httpx
import logging
import asyncio
from config import PLAYWRIGHT_SERVICE_URL

logger = logging.getLogger(__name__)

class ImageSearchService:
    
    @staticmethod
    async def search_images(query: str, max_results: int = 6) -> list[dict]:
        """
        Execute image search via Node.js Playwright service only.
        """
        try:
            return await asyncio.wait_for(
                ImageSearchService._execute_search(query, max_results),
                timeout=45.0
            )
        except asyncio.TimeoutError:
            logger.error(f"❌ Image search timed out for: {query}")
            return [{"error": "Search timed out after 45s"}]
        except Exception as e:
            logger.error(f"❌ Image search failed: {e}")
            return [{"error": str(e)}]

    @staticmethod
    async def _execute_search(query: str, max_results: int) -> list[dict]:
        """Execute the actual search via Node.js service"""
        
        
        try:
            logger.info(f"🖼️ Searching images via Node.js service: {query}")
            async with httpx.AsyncClient(timeout=40.0) as client:
                response = await client.post(
                    f"{PLAYWRIGHT_SERVICE_URL}/search-images",
                    json={"query": query, "max_results": max_results}
                )
                
                if response.status_code == 200:
                    results = response.json()
                    if results and isinstance(results, list):
                        logger.info(f"✅ Node.js service success: {len(results)} images")
                        return results
                    else:
                        logger.warning(f"⚠️ Node.js service returned empty results")
                        return [] # Return empty list instead of falling back
                else:
                    logger.warning(f"⚠️ Node.js service returned {response.status_code}")
                    return [{"error": f"Service error: {response.status_code}"}]
                    
        except httpx.ConnectError:
            logger.error("❌ Cannot connect to Playwright service")
            return [{"error": "Playwright service is not running"}]
        except Exception as e:
            logger.error(f"❌ Node.js image search failed: {e}")
            return [{"error": str(e)}]
