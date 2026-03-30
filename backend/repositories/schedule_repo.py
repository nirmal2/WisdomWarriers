from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.schedule import Schedule


async def create_schedule(db: AsyncSession, data: dict) -> Schedule:
    schedule = Schedule(**data)
    db.add(schedule)
    await db.flush()
    return schedule


async def list_schedules(db: AsyncSession) -> Sequence[Schedule]:
    result = await db.execute(select(Schedule).order_by(Schedule.created_at.desc()))
    return result.scalars().all()


async def get_schedule(db: AsyncSession, schedule_id: int) -> Optional[Schedule]:
    return await db.get(Schedule, schedule_id)


async def update_schedule(db: AsyncSession, schedule_id: int, data: dict) -> Optional[Schedule]:
    schedule = await db.get(Schedule, schedule_id)
    if schedule is None:
        return None
    for k, v in data.items():
        if v is not None:
            setattr(schedule, k, v)
    await db.flush()
    return schedule


async def delete_schedule(db: AsyncSession, schedule_id: int) -> bool:
    schedule = await db.get(Schedule, schedule_id)
    if schedule is None:
        return False
    await db.delete(schedule)
    await db.flush()
    return True


async def get_active_schedules(db: AsyncSession) -> Sequence[Schedule]:
    result = await db.execute(
        select(Schedule).where(Schedule.is_active == True, Schedule.cron_expr.isnot(None))
    )
    return result.scalars().all()
