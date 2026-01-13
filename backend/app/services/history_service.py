from sqlalchemy.orm import Session
from ..models.chat import ChatSession, ChatMessage
from datetime import datetime

class HistoryService:
    @staticmethod
    def create_session(db: Session, session_id: str, title: str = "New Chat"):
        """Create a new chat session"""
        session = ChatSession(id=session_id, title=title)
        db.add(session)
        db.commit()
        return session
    
    @staticmethod
    def get_session_history(db: Session, session_id: str, limit: int = 10):
        """Retrieve the last N messages of the session"""
        messages = db.query(ChatMessage)\
            .filter(ChatMessage.session_id == session_id)\
            .order_by(ChatMessage.timestamp.desc())\
            .limit(limit)\
            .all()
        return list(reversed(messages))  
    
    @staticmethod
    def add_message(db: Session, session_id: str, role: str, content: str):
        """Add a message to the history"""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content
        )
        db.add(message)
        db.commit()
        return message
    
    @staticmethod
    def get_session(db: Session, session_id: str):
        """Retrieve a session by its ID"""
        return db.query(ChatSession).filter(ChatSession.id == session_id).first()
