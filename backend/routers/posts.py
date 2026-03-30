from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.engine import get_db
from backend.schemas.post import PostListResponse, PostDetail
from backend.repositories.post_repo import list_posts, get_post_by_id, get_snapshots_by_url

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.get("", response_model=PostListResponse)
async def get_posts(
    username: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    likes_min: int | None = None,
    hashtag: str | None = None,
    tagged_group: str | None = None,
    period_label: str | None = None,
    sort: str = "likes_count",
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> PostListResponse:
    items, total = await list_posts(
        db, username, date_from, date_to, likes_min, hashtag, tagged_group, period_label, sort, limit, offset
    )
    return PostListResponse(items=items, total=total)


@router.get("/{post_id}", response_model=PostDetail)
async def get_post(post_id: str, db: AsyncSession = Depends(get_db)) -> PostDetail:
    post = await get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(404)
    snapshots = await get_snapshots_by_url(db, post.url)
    return PostDetail.model_validate({**post.__dict__, "snapshots": snapshots})
