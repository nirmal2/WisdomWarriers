from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.engine import get_db
from backend.schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleRead
from backend.repositories.schedule_repo import (
    create_schedule, list_schedules, get_schedule, update_schedule, delete_schedule
)
from backend.services.scheduler.jobs import register_schedule, unregister_schedule, run_scheduled_job

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


@router.get("", response_model=list[ScheduleRead])
async def get_schedules(db: AsyncSession = Depends(get_db)) -> list[ScheduleRead]:
    return await list_schedules(db)


@router.post("", response_model=ScheduleRead, status_code=201)
async def add_schedule(body: ScheduleCreate, db: AsyncSession = Depends(get_db)) -> ScheduleRead:
    schedule = await create_schedule(db, body.model_dump())
    await db.commit()
    if schedule.cron_expr and schedule.is_active:
        await register_schedule(schedule.id, schedule.cron_expr)
    return schedule


@router.get("/{schedule_id}", response_model=ScheduleRead)
async def get_one(schedule_id: int, db: AsyncSession = Depends(get_db)) -> ScheduleRead:
    schedule = await get_schedule(db, schedule_id)
    if not schedule:
        raise HTTPException(404)
    return schedule


@router.put("/{schedule_id}", response_model=ScheduleRead)
async def edit_schedule(
    schedule_id: int, body: ScheduleUpdate, db: AsyncSession = Depends(get_db)
) -> ScheduleRead:
    schedule = await update_schedule(db, schedule_id, body.model_dump(exclude_none=True))
    if not schedule:
        raise HTTPException(404)
    await db.commit()
    if schedule.cron_expr and schedule.is_active:
        await register_schedule(schedule.id, schedule.cron_expr)
    else:
        await unregister_schedule(schedule_id)
    return schedule


@router.delete("/{schedule_id}", status_code=204)
async def remove_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)) -> None:
    deleted = await delete_schedule(db, schedule_id)
    if not deleted:
        raise HTTPException(404)
    await db.commit()
    await unregister_schedule(schedule_id)


@router.post("/{schedule_id}/run-now", response_model=dict)
async def run_now(schedule_id: int) -> dict:
    await run_scheduled_job(schedule_id)
    return {"status": "triggered"}
