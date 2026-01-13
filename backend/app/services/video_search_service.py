"""
Video Search Service - Pure Node.js Playwright Implementation
"""

import httpx
import logging
import asyncio

logger = logging.getLogger(__name__)

class VideoSearchService:
    
    @staticmethod
    async def search_videos(query: str, max_results: int = 5) -> list[dict]:
        """
        Execute video search via Node.js Playwright service.
        """
        from config import PLAYWRIGHT_SERVICE_URL
        
        try:
            logger.info(f"🎬 Searching videos via Node.js service: {query}")
            async with httpx.AsyncClient(timeout=40.0) as client:
                response = await client.post(
                    f"{PLAYWRIGHT_SERVICE_URL}/search-videos",
                    json={"query": query, "max_results": max_results}
                )
                
                if response.status_code == 200:
                    results = response.json()
                    if results and isinstance(results, list):
                        logger.info(f"✅ Node.js video service success: {len(results)} videos")
                        return results
                    else:
                        logger.warning(f"⚠️ Node.js video service returned empty results")
                        return []
                else:
                    logger.warning(f"⚠️ Node.js video service returned {response.status_code}")
                    return [{"error": f"Service error: {response.status_code}"}]
                    
        except httpx.ConnectError:
            logger.error("❌ Cannot connect to Playwright service")
            return [{"error": "Playwright service is not running"}]
        except Exception as e:
            logger.error(f"❌ Node.js video search failed: {e}")
            return [{"error": str(e)}]
