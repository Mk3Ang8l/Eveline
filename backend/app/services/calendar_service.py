"""
Calendar Service - Database Backed
Manages calendar events with SQLAlchemy persistence.
"""

from datetime import datetime
from typing import List, Dict, Optional
import logging
from sqlalchemy.orm import Session

from ..core.database import SessionLocal
from ..models.all_models import CalendarEventDB

logger = logging.getLogger(__name__)


class CalendarService:
    @staticmethod
    def _parse_datetime(dt_str: str) -> datetime:
        """Parse datetime string in various formats"""
        formats = ["%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"]
        for fmt in formats:
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
        return datetime.strptime(dt_str[:10], "%Y-%m-%d")

    @classmethod
    def get_events(cls) -> List[Dict]:
        """Return all calendar events"""
        with SessionLocal() as db:
            events = db.query(CalendarEventDB).order_by(CalendarEventDB.start).all()
            return [
                {
                    "id": str(e.id),
                    "title": e.title,
                    "start": e.start.isoformat() if e.start else None,
                    "end": e.end.isoformat() if e.end else None,
                    "description": e.description or "",
                    "location": e.location or "",
                    "created_at": e.created_at.isoformat() if e.created_at else None
                }
                for e in events
            ]

    @classmethod
    def add_event(cls, title: str, start: str, end: Optional[str] = None, 
                  description: Optional[str] = None, location: Optional[str] = None) -> Dict:
        """Add a new event to the calendar"""
        with SessionLocal() as db:
            start_dt = cls._parse_datetime(start)
            end_dt = cls._parse_datetime(end) if end else start_dt
            
            new_event = CalendarEventDB(
                title=title,
                start=start_dt,
                end=end_dt,
                description=description or "",
                location=location or "",
                created_at=datetime.utcnow()
            )
            db.add(new_event)
            db.commit()
            db.refresh(new_event)
            
            return {
                "id": str(new_event.id),
                "title": new_event.title,
                "start": new_event.start.isoformat(),
                "end": new_event.end.isoformat() if new_event.end else None,
                "description": new_event.description,
                "location": new_event.location,
                "created_at": new_event.created_at.isoformat()
            }

    @classmethod
    def delete_event(cls, event_id: str) -> bool:
        """Delete an event by ID"""
        with SessionLocal() as db:
            event = db.query(CalendarEventDB).filter(CalendarEventDB.id == int(event_id)).first()
            if event:
                db.delete(event)
                db.commit()
                return True
            return False

    @classmethod
    def update_event(cls, event_id: str, updates: Dict) -> Optional[Dict]:
        """Update an existing event"""
        with SessionLocal() as db:
            event = db.query(CalendarEventDB).filter(CalendarEventDB.id == int(event_id)).first()
            if not event:
                return None
            
            if "title" in updates:
                event.title = updates["title"]
            if "start" in updates:
                event.start = cls._parse_datetime(updates["start"])
            if "end" in updates:
                event.end = cls._parse_datetime(updates["end"])
            if "description" in updates:
                event.description = updates["description"]
            if "location" in updates:
                event.location = updates["location"]
            
            db.commit()
            db.refresh(event)
            
            return {
                "id": str(event.id),
                "title": event.title,
                "start": event.start.isoformat(),
                "end": event.end.isoformat() if event.end else None,
                "description": event.description,
                "location": event.location
            }
