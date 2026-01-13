from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..models.all_models import NoteDB
from ..schemas.notes import NoteCreate, NoteUpdate

class NotesService:
    """Service for managing notes with CRUD operations"""
    
    @staticmethod
    def create_note(db: Session, note: NoteCreate) -> NoteDB:
        """Create a new note"""
        db_note = NoteDB(
            title=note.title,
            content=note.content,
            category=note.category or "General",
            tags=note.tags or "",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        return db_note
    
    @staticmethod
    def get_note(db: Session, note_id: int) -> Optional[NoteDB]:
        """Get a single note by ID"""
        return db.query(NoteDB).filter(NoteDB.id == note_id).first()
    
    @staticmethod
    def get_all_notes(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[NoteDB]:
        """Get all notes with optional filtering"""
        query = db.query(NoteDB)
        
        # Filter by category if provided
        if category:
            query = query.filter(NoteDB.category == category)
        
        # Search in title and content if search term provided
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (NoteDB.title.ilike(search_pattern)) | 
                (NoteDB.content.ilike(search_pattern)) |
                (NoteDB.tags.ilike(search_pattern))
            )
        
        return query.order_by(NoteDB.updated_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_note(db: Session, note_id: int, note_update: NoteUpdate) -> Optional[NoteDB]:
        """Update an existing note"""
        db_note = db.query(NoteDB).filter(NoteDB.id == note_id).first()
        if not db_note:
            return None
        
        # Update only provided fields
        update_data = note_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(db_note, field, value)
        
        db_note.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_note)
        return db_note
    
    @staticmethod
    def delete_note(db: Session, note_id: int) -> bool:
        """Delete a note"""
        db_note = db.query(NoteDB).filter(NoteDB.id == note_id).first()
        if not db_note:
            return False
        
        db.delete(db_note)
        db.commit()
        return True
    
    @staticmethod
    def get_categories(db: Session) -> List[str]:
        """Get all unique categories"""
        categories = db.query(NoteDB.category).distinct().all()
        return [cat[0] for cat in categories if cat[0]]
    
    @staticmethod
    def export_notes_as_text(db: Session, note_ids: Optional[List[int]] = None) -> str:
        """Export notes as formatted text"""
        if note_ids:
            notes = db.query(NoteDB).filter(NoteDB.id.in_(note_ids)).all()
        else:
            notes = db.query(NoteDB).order_by(NoteDB.created_at.desc()).all()
        
        export_text = "=" * 80 + "\n"
        export_text += "NOTES EXPORT\n"
        export_text += f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        export_text += f"Total Notes: {len(notes)}\n"
        export_text += "=" * 80 + "\n\n"
        
        for note in notes:
            export_text += f"Title: {note.title}\n"
            export_text += f"Category: {note.category}\n"
            if note.tags:
                export_text += f"Tags: {note.tags}\n"
            export_text += f"Created: {note.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            export_text += f"Updated: {note.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            export_text += "-" * 80 + "\n"
            export_text += note.content + "\n"
            export_text += "=" * 80 + "\n\n"
        
        return export_text
