from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel


class ScrapeRunRead(BaseModel):
    id: int
    scraper_type: str
    trigger: str
    schedule_id: Optional[int] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    embedding_status: str
    profiles_requested: int
    items_fetched: int
    error_message: Optional[str] = None
    embedding_error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class ScrapeRequest(BaseModel):
    scraper_type: str                       # 'posts' | 'profiles'
    usernames: Optional[list[str]] = None   # override profiles file
    batch_mode: bool = False
    results_limit: int = 100
    only_posts_newer_than: Optional[str] = None
    data_detail_level: Literal["basicData", "detailedData"] = "basicData"
    enable_embeddings: bool = True


class CombinedScrapeRequest(BaseModel):
    """Request for combined profile + post scrape"""
    usernames: Optional[list[str]] = None   # override profiles file
    batch_mode: bool = False
    results_limit: int = 100
    only_posts_newer_than: Optional[str] = None
    data_detail_level: Literal["basicData", "detailedData"] = "basicData"
    enable_embeddings: bool = True


class ScrapeStartRead(BaseModel):
    status: str
    profiles_count: int
    run_id: int
    action: Optional[str] = None


class ScrapeRunListResponse(BaseModel):
    items: list[ScrapeRunRead]
    total: int


class ProfilesSourceRead(BaseModel):
    usernames: list[str]


class ProfilesSourceUpdate(BaseModel):
    usernames: list[str]


class ScrapeProfileRead(BaseModel):
    id: int
    username: str
    category: Optional[str] = None
    grade: Optional[str] = None
    position: int
    profile_pic_url: Optional[str] = None

    model_config = {"from_attributes": True}


class ScrapeProfileCreate(BaseModel):
    username: str
    category: Optional[str] = None
    grade: Optional[str] = None


class ScrapeProfileBulkCreate(BaseModel):
    profiles: list[ScrapeProfileCreate]


class ScrapeProfileBulkResult(BaseModel):
    created: list[ScrapeProfileRead]
    skipped_existing: list[str] = []


class ScrapeProfileUpdate(BaseModel):
    username: Optional[str] = None
    category: Optional[str] = None
    grade: Optional[str] = None


class ScrapeDbUpdateStatus(BaseModel):
    posts_rows: int = 0
    profile_snapshots_rows: int = 0
    profiles_touched: int = 0
    missing_usernames: list[str] = []


class ScrapeStatusRead(BaseModel):
    run: Optional[ScrapeRunRead] = None
    progress_pct: int = 0
    db_updates: ScrapeDbUpdateStatus = ScrapeDbUpdateStatus()
    logs: list[str] = []


class CompareSummaryRead(BaseModel):
    run_a_profile_snapshot_rows: int = 0
    run_b_profile_snapshot_rows: int = 0
    run_a_latest_posts_rows: int = 0
    run_b_latest_posts_rows: int = 0
    common_profiles: int = 0
    new_profiles: int = 0
    missing_profiles: int = 0
    net_followers_delta: int = 0
    common_latest_posts: int = 0
    new_latest_posts: int = 0
    missing_latest_posts: int = 0
    net_likes_delta: int = 0


class ProfileDeltaRead(BaseModel):
    profile_id: str
    followers_run_a: int | None = None
    followers_run_b: int | None = None
    follows_run_a: int | None = None
    follows_run_b: int | None = None
    posts_run_a: int | None = None
    posts_run_b: int | None = None
    followers_delta: int = 0
    follows_delta: int = 0
    posts_delta: int = 0
    change_type: Literal["common", "new", "missing"]


class LatestPostDeltaRead(BaseModel):
    profile_id: str
    owner_username: str | None = None
    url: str
    likes_run_a: int | None = None
    likes_run_b: int | None = None
    comments_run_a: int | None = None
    comments_run_b: int | None = None
    views_run_a: int | None = None
    views_run_b: int | None = None
    likes_delta: int = 0
    comments_delta: int = 0
    views_delta: int = 0
    change_type: Literal["common", "new", "missing"]


class InsightRead(BaseModel):
    title: str
    value: str
    detail: str
    tone: Literal["positive", "negative", "neutral"] = "neutral"


class RunComparisonRead(BaseModel):
    run_a: ScrapeRunRead
    run_b: ScrapeRunRead
    summary: CompareSummaryRead
    profile_deltas: list[ProfileDeltaRead]
    latest_post_deltas: list[LatestPostDeltaRead]
    insights: list[InsightRead]
