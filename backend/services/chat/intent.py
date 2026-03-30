from backend.services.embedding.client import embed_texts
from backend.services.chat.tools import TOOL_DEFINITIONS


async def classify_intent(user_message: str) -> str:
    """Return one of: lookup | metric | comparison | trend | general"""
    msg = user_message.lower()
    if any(w in msg for w in ["compare", "vs ", " versus ", "difference between"]):
        return "comparison"
    if any(w in msg for w in ["trend", "over time", "last week", "last month", "growth"]):
        return "trend"
    if any(w in msg for w in ["top", "most", "highest", "best", "ranking", "average", "avg"]):
        return "metric"
    if any(w in msg for w in ["who is", "what is", "tell me about", "show me", "profile of"]):
        return "lookup"
    return "general"


async def embed_query(text: str) -> list[float]:
    vectors = await embed_texts([text])
    return vectors[0]
