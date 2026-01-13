"""
Script to initialize the notes table in the database
"""
from app.core.database import engine, Base
from app.models.all_models import NoteDB

def init_notes_table():
    """Create the notes table if it doesn't exist"""
    print("Creating notes table...")
    Base.metadata.create_all(bind=engine)
    print("✅ Notes table created successfully!")

if __name__ == "__main__":
    init_notes_table()
