from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ProfileBase(BaseModel):
    username: str
    url: Optional[str] = None
    full_name: Optional[str] = None
    biography: Optional[str] = None
    followers_count: int = 0
    follows_count: int = 0
    posts_count: int = 0
    is_verified: bool = False
    is_private: bool = False
    is_business_account: bool = False
    business_category: Optional[str] = None
    profile_pic_url: Optional[str] = None
    external_url: Optional[str] = None


class ProfileRead(ProfileBase):
    id: str
    igtv_video_count: int = 0
    highlight_reel_count: int = 0
    joined_recently: bool = False
    has_channel: bool = False
    first_seen_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SnapshotRead(BaseModel):
    id: int
    scraped_at: datetime
    followers_count: int
    follows_count: int
    posts_count: int
    period_label: str

    model_config = {"from_attributes": True}


class ProfileDetail(ProfileRead):
    snapshots: list[SnapshotRead] = []


class ProfileListResponse(BaseModel):
    items: list[ProfileRead]
    total: int
