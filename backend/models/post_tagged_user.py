from sqlalchemy import Column, Integer, Text, DateTime, func
from backend.db.base import Base


class PostTaggedUser(Base):
    __tablename__ = "post_tagged_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Text, nullable=False, index=True)
    run_id = Column(Integer, nullable=True, index=True)
    period_label = Column(Text, nullable=False, index=True)
    owner_username = Column(Text, nullable=True, index=True)
    tagged_user_raw = Column(Text, nullable=False)
    tagged_user_norm = Column(Text, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
