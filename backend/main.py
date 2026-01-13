import asyncio
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Import startup checks
from app.utils.startup_checks import startup_checks

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup checks
    startup_checks()

    # Create DB tables
    from app.core.database import Base, engine
    from app.models.chat import ChatSession, ChatMessage
    Base.metadata.create_all(bind=engine)
    
    yield
    # Shutdown steps here if needed

# Initialize FastAPI with lifespan
app = FastAPI(title="TERMINAL_OS Backend", version="2.0.0", lifespan=lifespan)

# Standard CORS - Required for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Simplified for dev stability
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure data/uploads exists and mount it
UPLOAD_DIR = "data/uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/")
def root():
    return {"status": "Minimal Mode", "ok": True}

# Import and include routers
from app.routers import ai, sandbox, accounts, memory, calendar, crypto, notes, realtime, vision

app.include_router(ai.router, prefix="/api", tags=["ai"])
app.include_router(sandbox.router, prefix="/api/sandbox", tags=["sandbox"])
app.include_router(accounts.router, prefix="/api", tags=["accounts"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"])
app.include_router(crypto.router, prefix="/api/crypto", tags=["crypto"])
app.include_router(notes.router, prefix="/api", tags=["notes"])
app.include_router(realtime.router, prefix="/api", tags=["realtime"])
app.include_router(vision.router, prefix="/api/vision", tags=["vision"])

if __name__ == "__main__":
    import uvicorn
    import os
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)
