from sqlalchemy import Column, Text, Integer, Boolean, DateTime, func
from pgvector.sqlalchemy import Vector
from backend.db.base import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Text, primary_key=True)            # Instagram numeric ID
    username = Column(Text, unique=True, nullable=False, index=True)
    url = Column(Text)
    full_name = Column(Text)
    biography = Column(Text)
    followers_count = Column(Integer, default=0)
    follows_count = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)
    igtv_video_count = Column(Integer, default=0)
    has_channel = Column(Boolean, default=False)
    highlight_reel_count = Column(Integer, default=0)
    is_business_account = Column(Boolean, default=False)
    joined_recently = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_private = Column(Boolean, default=False)
    business_category = Column(Text)
    profile_pic_url = Column(Text)
    profile_pic_url_hd = Column(Text)
    external_url = Column(Text)
    fbid = Column(Text)
    first_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    embedding = Column(Vector(1536))
