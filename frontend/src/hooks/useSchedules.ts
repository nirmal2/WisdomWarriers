import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { fetchSchedules, createSchedule, updateSchedule, deleteSchedule, runScheduleNow } from "../api/schedules"
import type { ScheduleCreate } from "../types/schedule"

export function useSchedules() {
  return useQuery({ queryKey: ["schedules"], queryFn: fetchSchedules })
}

export function useCreateSchedule() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: ScheduleCreate) => createSchedule(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["schedules"] }),
  })
}

export function useUpdateSchedule() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: Partial<ScheduleCreate> }) => updateSchedule(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["schedules"] }),
  })
}

export function useDeleteSchedule() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteSchedule(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["schedules"] }),
  })
}

export function useRunNow() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => runScheduleNow(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["schedules"] }),
  })
}
