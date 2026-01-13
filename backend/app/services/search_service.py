import httpx
import logging

logger = logging.getLogger(__name__)

from config import PLAYWRIGHT_SERVICE_URL

class SearchService:
    @staticmethod
    def search(query: str, region: str = "wt-wt", max_results: int = 5) -> list[dict]:
        """
        Search using Node.js Playwright service.
        """
        logger.info(f"🔍 Searching via Node.js service: {query}")
        
        try:
            response = httpx.post(
                f"{PLAYWRIGHT_SERVICE_URL}/search",
                json={"query": query, "max_results": max_results},
                timeout=30.0
            )
            
            if response.status_code == 200:
                results = response.json()
                logger.info(f"✅ Got {len(results)} results from Node.js service")
                return results
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', f"Unknown error {response.status_code}")
                except:
                    error_msg = f"Service error: {response.status_code}"
                
                logger.error(f"❌ Node.js service error: {error_msg}")
                return [{"title": "Error", "href": "", "body": error_msg}]
                
        except httpx.ConnectError:
            logger.error("❌ Cannot connect to Playwright service. Is it running?")
            return [{"title": "Error", "href": "", "body": "Playwright service not running. Start it with: cd playwright-service && npm start"}]
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return [{"title": "Error", "href": "", "body": f"Search failed: {str(e)}"}]
