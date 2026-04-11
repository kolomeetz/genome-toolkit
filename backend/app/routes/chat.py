"""Chat SSE endpoint — streams Agent SDK responses to the frontend."""
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from backend.app.main import users_db
from backend.app.agent.agent import create_agent_session, stream_agent_response, build_system_prompt

router = APIRouter(prefix="/api")

# In-memory store of active agent clients per session
# For single-user self-hosted, this is fine
_active_clients: dict = {}


class ChatRequest(BaseModel):
    session_id: str
    message: str
    page_context: str | None = None


@router.post("/chat")
async def chat(req: ChatRequest):
    session = await users_db.get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save user message
    await users_db.save_message(req.session_id, "user", req.message)
    await users_db.touch_session(req.session_id)

    # Auto-set session title from first user message
    session_data = await users_db.get_session(req.session_id)
    if session_data and not session_data.get('title'):
        # Use first 60 chars of first message as title
        title = req.message[:60].strip()
        if len(req.message) > 60:
            title = title.rsplit(' ', 1)[0] + '...'
        await users_db.update_session(req.session_id, title=title)

    if req.page_context:
        # Extract view name from first line "You are on the X page."
        first_line = req.page_context.split('\n')[0] if req.page_context else ''
        view_tag = ''
        if 'RISK' in first_line: view_tag = 'risk'
        elif 'MENTAL HEALTH' in first_line: view_tag = 'mental-health'
        elif 'PGX' in first_line: view_tag = 'pgx'
        elif 'ADDICTION' in first_line: view_tag = 'addiction'
        elif 'SNP' in first_line: view_tag = 'snps'
        if view_tag:
            await users_db.update_session(req.session_id, view_context=view_tag)

    async def get_or_create_client(session_id: str, page_context: str | None = None):
        """Get existing client or create new one. Handles stale connections."""
        client = _active_clients.get(session_id)
        if client is not None:
            # Update system prompt with fresh page context
            if page_context:
                client.options.system_prompt = build_system_prompt(page_context)
            return client

        client, _ = await create_agent_session(page_context=page_context)
        await client.connect()
        _active_clients[session_id] = client
        return client

    async def event_stream():
        text_parts = []
        try:
            client = await get_or_create_client(req.session_id, req.page_context)
            async for event in stream_agent_response(client, req.message):
                if event["event"] == "text_delta":
                    text_parts.append(event["data"]["content"])
                elif event["event"] == "session_init":
                    agent_sid = event["data"].get("agent_session_id")
                    if agent_sid:
                        await users_db.set_agent_session(req.session_id, agent_sid)

                yield {
                    "event": event["event"],
                    "data": json.dumps(event["data"]),
                }
        except Exception as e:
            # Remove stale client on connection errors
            _active_clients.pop(req.session_id, None)
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)}),
            }
        finally:
            full_text = "".join(text_parts)
            if full_text:
                await users_db.save_message(req.session_id, "assistant", full_text)

    return EventSourceResponse(event_stream())
