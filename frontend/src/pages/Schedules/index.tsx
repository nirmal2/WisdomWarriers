import { useState } from "react"
import { useSchedules, useCreateSchedule, useDeleteSchedule, useUpdateSchedule, useRunNow } from "../../hooks/useSchedules"
import { ScheduleModal } from "./ScheduleModal"
import { ScheduleList } from "./ScheduleList"
import type { Schedule, ScheduleCreate } from "../../types/schedule"

export default function SchedulesPage() {
  const [showModal, setShowModal] = useState(false)
  const [editingSchedule, setEditingSchedule] = useState<Schedule | null>(null)
  const { data: schedules = [] } = useSchedules()
  const create = useCreateSchedule()
  const remove = useDeleteSchedule()
  const update = useUpdateSchedule()
  const runNow = useRunNow()

  const handleCreate = (data: ScheduleCreate) => {
    create.mutate(data, { onSuccess: () => setShowModal(false) })
  }

  const handleEdit = (data: ScheduleCreate) => {
    if (!editingSchedule) return
    update.mutate({ id: editingSchedule.id, body: data }, { onSuccess: () => setEditingSchedule(null) })
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Schedules</h1>
        <button
          onClick={() => setShowModal(true)}
          className="px-3 py-1.5 text-sm bg-blue-700 hover:bg-blue-600 rounded-lg transition-colors"
        >
          + New Schedule
        </button>
      </div>
      <ScheduleList
        schedules={schedules}
        onDelete={id => remove.mutate(id)}
        onToggle={(id, active) => update.mutate({ id, body: { is_active: active } })}
        onRunNow={id => runNow.mutate(id)}
        onEdit={s => setEditingSchedule(s)}
      />
      {showModal && <ScheduleModal onSubmit={handleCreate} onClose={() => setShowModal(false)} />}
      {editingSchedule && (
        <ScheduleModal
          initialData={editingSchedule}
          onSubmit={handleEdit}
          onClose={() => setEditingSchedule(null)}
        />
      )}
    </div>
  )
}
