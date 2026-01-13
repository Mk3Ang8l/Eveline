"""
AI Router - Chat and scraping endpoints
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ..schemas.all_schemas import ChatRequest, ScrapeRequest, ChatResponse
from ..services.ai_service import AIService
from ..services.scraping_service import ScrapingService
from ..services.history_service import HistoryService
from ..core.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
import logging
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat")
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """Stream AI chat response with persistent history"""
    
    # Session Management
    if not request.session_id:
        request.session_id = str(uuid.uuid4())
        HistoryService.create_session(db, request.session_id)
    else:
        # Check if exists, if not create
        session = HistoryService.get_session(db, request.session_id)
        if not session:
             HistoryService.create_session(db, request.session_id)

    return StreamingResponse(
        AIService.get_chat_response_stream(request.message, request.session_id, db, request.context),
        media_type="text/event-stream"
    )


@router.post("/scrape")
async def scrape_endpoint(request: ScrapeRequest):
    """Scrape content from URL"""
    try:
        content = ScrapingService.scrape_url(request.url)
        return {"title": "Scraped Content", "extracted_data": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
