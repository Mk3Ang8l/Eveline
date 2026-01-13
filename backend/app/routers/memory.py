from fastapi import APIRouter
from ..services.memory_service import MemoryService
from pydantic import BaseModel
from typing import List, Dict

router = APIRouter()

class PreferenceUpdate(BaseModel):
    key: str
    value: str

@router.get("/recent-topics")
def get_recent_topics():
    """Get topics discussed recently"""
    return {"topics": MemoryService.get_recent_topics()}

@router.get("/preferences")
def get_preferences():
    """Get all user preferences"""
    return MemoryService.get_all_preferences()

@router.post("/preferences")
def set_preference(pref: PreferenceUpdate):
    """Set a user preference"""
    MemoryService.save_preference(pref.key, pref.value)
    return {"status": "saved", "key": pref.key}

@router.get("/search")
def search_memory(q: str):
    """Search conversation history"""
    results = MemoryService.search_memory(q, limit=5)
    return {"results": results}

@router.get("/facts/{topic}")
def get_facts(topic: str):
    """Get learned facts about a topic"""
    facts = MemoryService.get_facts_about(topic)
    return {"topic": topic, "facts": facts}
