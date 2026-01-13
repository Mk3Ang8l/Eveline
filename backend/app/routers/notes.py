from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from io import BytesIO

from ..core.database import get_db
from ..schemas.notes import NoteCreate, NoteUpdate, NoteResponse
from ..services.notes_service import NotesService

router = APIRouter()

@router.post("/notes", response_model=NoteResponse, status_code=201)
def create_note(
    note: NoteCreate,
    db: Session = Depends(get_db)
):
    """Create a new note"""
    return NotesService.create_note(db, note)

@router.get("/notes", response_model=List[NoteResponse])
def get_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all notes with optional filtering
    - **skip**: Number of notes to skip (pagination)
    - **limit**: Maximum number of notes to return
    - **category**: Filter by category
    - **search**: Search in title, content, and tags
    """
    return NotesService.get_all_notes(db, skip, limit, category, search)

@router.get("/notes/{note_id}", response_model=NoteResponse)
def get_note(
    note_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific note by ID"""
    note = NotesService.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@router.put("/notes/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: int,
    note_update: NoteUpdate,
    db: Session = Depends(get_db)
):
    """Update a note"""
    note = NotesService.update_note(db, note_id, note_update)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@router.delete("/notes/{note_id}", status_code=204)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db)
):
    """Delete a note"""
    success = NotesService.delete_note(db, note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return Response(status_code=204)

@router.get("/notes-categories", response_model=List[str])
def get_categories(db: Session = Depends(get_db)):
    """Get all unique note categories"""
    return NotesService.get_categories(db)

@router.get("/notes-export")
def export_notes(
    note_ids: Optional[str] = Query(None, description="Comma-separated note IDs to export"),
    db: Session = Depends(get_db)
):
    """
    Export notes as a text file
    - **note_ids**: Optional comma-separated list of note IDs to export (exports all if not provided)
    """
    # Parse note IDs if provided
    ids_list = None
    if note_ids:
        try:
            ids_list = [int(id.strip()) for id in note_ids.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid note IDs format")
    
    # Generate export text
    export_text = NotesService.export_notes_as_text(db, ids_list)
    
    # Create a BytesIO object for the file
    file_buffer = BytesIO(export_text.encode('utf-8'))
    file_buffer.seek(0)
    
    # Return as downloadable file
    return StreamingResponse(
        file_buffer,
        media_type="text/plain",
        headers={
            "Content-Disposition": "attachment; filename=notes_export.txt"
        }
    )
