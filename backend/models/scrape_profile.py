from sqlalchemy import Column, Integer, Text, DateTime, func
from backend.db.base import Base


class ScrapeProfile(Base):
    __tablename__ = "scrape_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(Text, nullable=False, unique=True, index=True)
    category = Column(Text, nullable=True)
    grade = Column(Text, nullable=True)
    position = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())