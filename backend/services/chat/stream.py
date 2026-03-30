import json
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession
from openai.types.chat import ChatCompletionMessageParam
from backend.services.embedding.client import get_openai_client
from backend.services.chat.tools import TOOL_DEFINITIONS, dispatch_tool
from backend.services.chat.context_builder import retrieve_similar, build_system_prompt
from backend.services.chat.intent import classify_intent, embed_query
from backend.schemas.chat import ChatMessage, SourceItem


async def stream_chat_response(
    db: AsyncSession,
    messages: list[ChatMessage],
) -> AsyncIterator[tuple[str, list[SourceItem]]]:
    client = get_openai_client()
    user_text = messages[-1].content

    intent = await classify_intent(user_text)
    query_vec = await embed_query(user_text)
    context_parts, sources = await retrieve_similar(db, query_vec)
    system_prompt = build_system_prompt(context_parts)

    history: list[ChatCompletionMessageParam] = [{"role": "system", "content": system_prompt}]
    for m in messages:
        history.append({"role": m.role, "content": m.content})

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=history,
        tools=TOOL_DEFINITIONS,
        tool_choice="auto",
        stream=True,
    )

    tool_calls_buf: dict[int, dict] = {}
    text_buf = []

    async for chunk in response:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta is None:
            continue

        if delta.tool_calls:
            for tc in delta.tool_calls:
                idx = tc.index
                if idx not in tool_calls_buf:
                    tool_calls_buf[idx] = {"id": tc.id or "", "name": "", "arguments": ""}
                if tc.function:
                    if tc.function.name:
                        tool_calls_buf[idx]["name"] += tc.function.name
                    if tc.function.arguments:
                        tool_calls_buf[idx]["arguments"] += tc.function.arguments

        if delta.content:
            text_buf.append(delta.content)
            yield delta.content, sources

    # Execute any tool calls and do a follow-up non-stream call
    if tool_calls_buf:
        tool_messages: list[ChatCompletionMessageParam] = []
        for tc in tool_calls_buf.values():
            args = json.loads(tc["arguments"] or "{}")
            tool_result = await dispatch_tool(tc["name"], args, db)
            tool_messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps(tool_result),
            })
        history.append({"role": "assistant", "tool_calls": [
            {"id": tc["id"], "type": "function", "function": {"name": tc["name"], "arguments": tc["arguments"]}}
            for tc in tool_calls_buf.values()
        ]})
        history.extend(tool_messages)
        followup = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=history,
            stream=True,
        )
        async for chunk in followup:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content, sources
