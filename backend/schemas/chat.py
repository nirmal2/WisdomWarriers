from typing import Optional, Any
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str       # 'user' | 'assistant'
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    session_id: Optional[str] = None


class SourceItem(BaseModel):
    type: str       # 'profile' | 'post'
    username: Optional[str] = None
    url: Optional[str] = None
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem] = []
    session_id: str
