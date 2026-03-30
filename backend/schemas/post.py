from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class PostRead(BaseModel):
    id: str
    source_post_id: Optional[str] = None
    short_code: Optional[str] = None
    owner_username: Optional[str] = None
    owner_full_name: Optional[str] = None
    owner_id: Optional[str] = None
    owner_profile_pic_url: Optional[str] = None
    location_name: Optional[str] = None
    location_id: Optional[str] = None
    url: str
    timestamp: Optional[datetime] = None
    likes_count: int = 0
    video_play_count: int = 0
    video_view_count: int = 0
    type: Optional[str] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    video_duration: Optional[float] = None
    display_url: Optional[str] = None
    display_storage_path: Optional[str] = None
    display_storage_url: Optional[str] = None
    dimensions_height: Optional[int] = None
    dimensions_width: Optional[int] = None
    is_comments_disabled: bool = False
    alt: Optional[str] = None
    caption: Optional[str] = None
    product_type: Optional[str] = None
    input_url: Optional[str] = None
    comments_count: int = 0
    first_comment: Optional[str] = None
    latest_comments: list[Any] = []
    images: list[Any] = []
    child_posts: list[Any] = []
    music_info: dict[str, Any] = {}
    hashtags: list[Any] = []
    mentions: list[Any] = []
    tagged_users: list[Any] = []
    coauthor_producers: list[Any] = []
    is_pinned: bool = False
    profile_id: Optional[str] = None
    scraped_at: Optional[datetime] = None
    period_label: str
    run_id: Optional[int] = None
    embedding: Optional[list[float]] = None

    model_config = {"from_attributes": True}


class PostListResponse(BaseModel):
    items: list[PostRead]
    total: int


class PostSnapshotRead(BaseModel):
    id: int
    run_id: Optional[int] = None
    scraped_at: datetime
    likes_count: int = 0
    video_play_count: int = 0
    type: Optional[str] = None
    video_url: Optional[str] = None
    display_url: Optional[str] = None
    display_storage_path: Optional[str] = None
    display_storage_url: Optional[str] = None
    caption: Optional[str] = None
    product_type: Optional[str] = None
    period_label: str

    model_config = {"from_attributes": True}


class PostDetail(PostRead):
    snapshots: list[PostSnapshotRead] = []
