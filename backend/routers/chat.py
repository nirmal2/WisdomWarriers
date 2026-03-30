import json
import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.engine import get_db
from backend.schemas.chat import ChatRequest
from backend.services.chat.stream import stream_chat_response

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    session_id = req.session_id or str(uuid.uuid4())
    sources_sent = False

    async def event_stream():
        nonlocal sources_sent
        async for text_chunk, sources in stream_chat_response(db, req.messages):
            if not sources_sent:
                sources_payload = json.dumps({
                    "type": "sources",
                    "data": [s.model_dump() for s in sources],
                    "session_id": session_id,
                })
                yield f"data: {sources_payload}\n\n"
                sources_sent = True
            yield f"data: {json.dumps({'type': 'text', 'content': text_chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
