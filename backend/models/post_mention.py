from sqlalchemy import Column, Integer, Text, DateTime, func
from backend.db.base import Base


class PostMention(Base):
    __tablename__ = "post_mentions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Text, nullable=False, index=True)
    run_id = Column(Integer, nullable=True, index=True)
    period_label = Column(Text, nullable=False, index=True)
    owner_username = Column(Text, nullable=True, index=True)
    mention_raw = Column(Text, nullable=False)
    mention_norm = Column(Text, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
