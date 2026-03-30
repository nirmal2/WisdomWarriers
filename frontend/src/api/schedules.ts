import { API_URL } from "../config"
import type { Schedule, ScheduleCreate } from "../types/schedule"

export const fetchSchedules = (): Promise<Schedule[]> =>
  fetch(`${API_URL}/api/schedules`).then(r => r.json())

export const createSchedule = (body: ScheduleCreate): Promise<Schedule> =>
  fetch(`${API_URL}/api/schedules`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then(r => r.json())

export const updateSchedule = (id: number, body: Partial<ScheduleCreate>): Promise<Schedule> =>
  fetch(`${API_URL}/api/schedules/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then(r => r.json())

export const deleteSchedule = (id: number): Promise<void> =>
  fetch(`${API_URL}/api/schedules/${id}`, { method: "DELETE" }).then(() => {})

export const runScheduleNow = (id: number): Promise<{ status: string }> =>
  fetch(`${API_URL}/api/schedules/${id}/run-now`, { method: "POST" }).then(r => r.json())
