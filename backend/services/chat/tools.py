from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from backend.repositories.analytics_repo import (
    get_top_profiles,
    get_follower_growth,
    get_hashtag_frequency,
    get_engagement_by_profile,
)


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_top_profiles",
            "description": "Get top Instagram profiles ranked by a metric",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric": {"type": "string", "enum": ["followers_count", "follows_count", "posts_count"]},
                    "limit": {"type": "integer", "default": 10},
                },
                "required": ["metric"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_profile_growth",
            "description": "Get follower growth over time for a profile",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {"type": "string"},
                },
                "required": ["username"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_trending_hashtags",
            "description": "Get most used hashtags across all posts",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 20},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_post_performance",
            "description": "Get average likes and plays per profile",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


async def dispatch_tool(name: str, args: dict[str, Any], db: AsyncSession) -> Any:
    if name == "get_top_profiles":
        return await get_top_profiles(db, args.get("metric", "followers_count"), args.get("limit", 10))
    if name == "get_profile_growth":
        return await get_follower_growth(db, args.get("username"))
    if name == "get_trending_hashtags":
        return await get_hashtag_frequency(db, args.get("limit", 20))
    if name == "get_post_performance":
        return await get_engagement_by_profile(db)
    return {"error": "unknown tool"}
