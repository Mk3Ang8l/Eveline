from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from datetime import datetime
from ..core.database import Base

class TaskDB(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    status = Column(String, default="PENDING")
    priority = Column(String, default="MED")
    deadline = Column(String)

class TransactionDB(Base):
    __tablename__ = "finance"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String)
    description = Column(String)
    category = Column(String)
    amount = Column(Float)

class NoteDB(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String, default="General")
    tags = Column(String, default="") 
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CalendarEventDB(Base):
    __tablename__ = "calendar_events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=True)
    description = Column(Text, default="")
    location = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

