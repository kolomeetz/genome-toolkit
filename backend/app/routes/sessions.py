"""Session management routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.main import users_db

router = APIRouter(prefix="/api")


class UpdateSessionRequest(BaseModel):
    title: str | None = None
    view_context: str | None = None


@router.post("/sessions")
async def create_session():
    return await users_db.create_session()


@router.get("/sessions")
async def list_sessions(limit: int = 50, offset: int = 0):
    return await users_db.list_sessions(limit=limit, offset=offset)


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    session = await users_db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = await users_db.get_messages(session_id)
    return {**session, "messages": messages}


@router.patch("/sessions/{session_id}")
async def update_session(session_id: str, req: UpdateSessionRequest):
    session = await users_db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    updates = {}
    if req.title is not None:
        updates['title'] = req.title
    if req.view_context is not None:
        updates['view_context'] = req.view_context
    if updates:
        await users_db.update_session(session_id, **updates)
    return await users_db.get_session(session_id)


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    session = await users_db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await users_db.delete_session(session_id)
    return {"deleted": True}
