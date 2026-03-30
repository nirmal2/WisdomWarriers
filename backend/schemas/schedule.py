from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ScheduleBase(BaseModel):
    name: str
    scraper_type: str
    frequency: str                              # 'daily' | 'weekly' | 'monthly' | 'on_demand'
    cron_expr: Optional[str] = None
    is_active: bool = True
    batch_mode: bool = False
    results_limit: int = 27
    only_posts_newer_than: Optional[str] = None
    actor_id: Optional[str] = None


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    frequency: Optional[str] = None
    cron_expr: Optional[str] = None
    is_active: Optional[bool] = None
    batch_mode: Optional[bool] = None
    results_limit: Optional[int] = None
    only_posts_newer_than: Optional[str] = None


class ScheduleRead(ScheduleBase):
    id: int
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
