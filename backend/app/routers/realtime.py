from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
from ..services.realtime_service import RealtimeService
import asyncio
import json

router = APIRouter(prefix="/realtime", tags=["Realtime"])

@router.get("/events")
async def get_latest_events():
    """Get the current buffer of real-time events."""
    return RealtimeService.get_events()

@router.post("/start")
async def start_stream():
    """Start the CertStream background task."""
    await RealtimeService.start_certstream()
    return {"status": "started", "message": "CertStream connection initiated"}

@router.post("/stop")
async def stop_stream():
    """Stop the CertStream background task."""
    await RealtimeService.stop_certstream()
    return {"status": "stopped", "message": "CertStream connection closed"}

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for live data streaming to the frontend.
    Broadcasts new events as they arrive.
    """
    await websocket.accept()
    # Initial state: Send current buffer
    initial_events = RealtimeService.get_events()
    await websocket.send_json({"type": "INIT", "data": initial_events})
    
    # Simple broadcast loop
    # For now, we poll the service buffer for simplicity
    # In a production app, we would use a proper PubSub or Queue
    last_count = len(initial_events)
    try:
        while True:
            await asyncio.sleep(1) # Poll for new items every second
            current_events = RealtimeService.get_events()
            if len(current_events) > last_count:
                # Send only the new events
                new_items = current_events[last_count:]
                await websocket.send_json({"type": "UPDATE", "data": new_items})
                last_count = len(current_events)
            elif len(current_events) < last_count:
                # Buffer was cleared/wrapped
                last_count = len(current_events)
    except WebSocketDisconnect:
        pass
