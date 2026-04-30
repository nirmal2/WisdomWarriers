from sqlalchemy import Column, Integer, Text, DateTime, func
from backend.db.base import Base


class PostSnapshotHashtag(Base):
    __tablename__ = "post_snapshot_hashtags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(Integer, nullable=False, index=True)
    post_id = Column(Text, nullable=False, index=True)
    run_id = Column(Integer, nullable=True, index=True)
    period_label = Column(Text, nullable=False, index=True)
    owner_username = Column(Text, nullable=True, index=True)
    hashtag_raw = Column(Text, nullable=False)
    hashtag_norm = Column(Text, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
