import httpx
import logging

logger = logging.getLogger(__name__)

from config import PLAYWRIGHT_SERVICE_URL

class ScrapingService:
    @staticmethod
    async def scrape_url(url: str, save_session: bool = False) -> str:
        """
        Scrape URL using Node.js Playwright service.
        """
        logger.info(f"🌐 Scraping via Node.js service: {url}")
        
        try:
            async with httpx.AsyncClient(timeout=40.0) as client:
                response = await client.post(
                    f"{PLAYWRIGHT_SERVICE_URL}/scrape",
                    json={"url": url}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    text = data.get("text", "")
                    logger.info(f"✅ Scraped {len(text)} characters")
                    return text
                else:
                    logger.error(f"❌ Node.js service returned {response.status_code}")
                    return f"Service error: {response.status_code}"
                    
        except httpx.ConnectError:
            logger.error("❌ Cannot connect to Playwright service")
            return "ERROR: Playwright service not running. Start it with: cd playwright-service && npm start"
        except Exception as e:
            logger.error(f"❌ Scraping failed: {e}")
            return f"Scraping failed: {str(e)}"
