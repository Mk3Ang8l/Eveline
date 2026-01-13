"""
Sandbox Router - API endpoints for code and command execution
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
from ..services.sandbox_service import SandboxService

router = APIRouter()


class SandboxRequest(BaseModel):
    code: str = None
    command: str = None


@router.post("/run")
async def run_in_sandbox(request: SandboxRequest):
    """Execute code or command in the sandbox (non-streaming)"""
    if request.code:
        result = SandboxService.execute_code(request.code)
        return {"type": "code_execution", "output": result}
    
    if request.command:
        result = SandboxService.execute_command(request.command)
        return {"type": "shell_execution", "output": result}
        
    raise HTTPException(status_code=400, detail="No code or command provided")


@router.get("/stream")
async def stream_command(command: str):
    """
    Stream command output in real-time via Server-Sent Events (SSE).
    Usage: GET /api/sandbox/stream?command=ping%20google.com%20-c%205
    """
    async def generate():
        for line in SandboxService.execute_command_stream(command):
            yield f"data: {json.dumps({'line': line})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )
