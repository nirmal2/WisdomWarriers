from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


SELECTED_POST_FIELDS = {
    "videoPlayCount", "url", "timestamp", "ownerFullName",
    "likesCount", "inputUrl", "hashtags", "coauthorProducers", "ownerUsername",
    "type", "videoUrl", "displayUrl", "caption", "productType",
    "ownerProfilePicUrl", "ownerId", "videoViewCount", "audioUrl", "videoDuration",
    "dimensionsHeight", "dimensionsWidth", "isCommentsDisabled", "alt", "musicInfo",
    "images", "childPosts", "latestComments", "commentsCount", "shortCode",
    "mentions", "firstComment", "taggedUsers", "isPinned", "locationName", "locationId", "id",
}


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def normalize_post(raw: dict[str, Any]) -> dict[str, Any]:
    owner = raw.get("owner") or {}
    latest_comments = raw.get("latestComments") or []
    comments_count = raw.get("commentsCount")
    if comments_count is None:
        comments_count = len(latest_comments)

    return {
        "source_post_id": str(raw.get("id")) if raw.get("id") is not None else None,
        "short_code": raw.get("shortCode"),
        "owner_username": raw.get("ownerUsername"),
        "owner_full_name": raw.get("ownerFullName"),
        "owner_id": raw.get("ownerId") or owner.get("id"),
        "owner_profile_pic_url": raw.get("ownerProfilePicUrl") or owner.get("profile_pic_url"),
        "location_name": raw.get("locationName"),
        "location_id": str(raw.get("locationId")) if raw.get("locationId") is not None else None,
        "url": raw.get("url", ""),
        "timestamp": _parse_ts(raw.get("timestamp")),
        "likes_count": raw.get("likesCount", 0) or 0,
        "video_play_count": raw.get("videoPlayCount", 0) or 0,
        "video_view_count": raw.get("videoViewCount", 0) or 0,
        "type": raw.get("type"),
        "video_url": raw.get("videoUrl"),
        "audio_url": raw.get("audioUrl"),
        "video_duration": raw.get("videoDuration"),
        "display_url": raw.get("displayUrl"),
        "dimensions_height": raw.get("dimensionsHeight"),
        "dimensions_width": raw.get("dimensionsWidth"),
        "is_comments_disabled": bool(raw.get("isCommentsDisabled", False)),
        "alt": raw.get("alt"),
        "caption": raw.get("caption"),
        "product_type": raw.get("productType"),
        "input_url": raw.get("inputUrl"),
        "comments_count": comments_count or 0,
        "first_comment": raw.get("firstComment"),
        "latest_comments": latest_comments,
        "images": raw.get("images") or [],
        "child_posts": raw.get("childPosts") or [],
        "music_info": raw.get("musicInfo") or {},
        "hashtags": raw.get("hashtags") or [],
        "mentions": raw.get("mentions") or [],
        "tagged_users": raw.get("taggedUsers") or [],
        "coauthor_producers": raw.get("coauthorProducers") or [],
        "is_pinned": bool(raw.get("isPinned", False)),
    }


def normalize_profile(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(raw.get("id", "")),
        "username": raw.get("username", ""),
        "url": raw.get("url"),
        "full_name": raw.get("fullName"),
        "biography": raw.get("biography"),
        "followers_count": raw.get("followersCount", 0) or 0,
        "follows_count": raw.get("followsCount", 0) or 0,
        "posts_count": raw.get("postsCount", 0) or 0,
        "igtv_video_count": raw.get("igtvVideoCount", 0) or 0,
        "has_channel": raw.get("hasChannel", False),
        "highlight_reel_count": raw.get("highlightReelCount", 0) or 0,
        "is_business_account": raw.get("isBusinessAccount", False),
        "joined_recently": raw.get("joinedRecently", False),
        "is_verified": raw.get("verified", False),
        "is_private": raw.get("private", False),
        "business_category": raw.get("businessCategoryName"),
        "profile_pic_url": raw.get("profilePicUrl"),
        "profile_pic_url_hd": raw.get("profilePicUrlHD"),
        "external_url": raw.get("externalUrl"),
        "fbid": raw.get("fbid"),
    }
