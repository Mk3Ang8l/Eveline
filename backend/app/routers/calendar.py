from fastapi import APIRouter, HTTPException
from ..services.calendar_service import CalendarService
from ..schemas.all_schemas import CalendarEventCreate, CalendarEventUpdate
from typing import List, Dict

router = APIRouter()

@router.get("/events")
def list_events():
    """List all calendar events"""
    return CalendarService.get_events()

@router.post("/events")
def add_event(event: CalendarEventCreate):
    """Add a new event"""
    return CalendarService.add_event(
        title=event.title,
        start=event.start,
        end=event.end,
        description=event.description,
        location=event.location
    )

@router.delete("/events/{event_id}")
def delete_event(event_id: str):
    """Delete an event"""
    success = CalendarService.delete_event(event_id)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"status": "deleted", "id": event_id}

@router.patch("/events/{event_id}")
def update_event(event_id: str, updates: CalendarEventUpdate):
    """Update an existing event"""
    updated = CalendarService.update_event(event_id, updates.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Event not found")
    return updated
