import type { Schedule } from "../../types/schedule"
import { StatusBadge } from "../../components/StatusBadge"
import { format } from "date-fns"

interface Props {
  schedules: Schedule[]
  onDelete: (id: number) => void
  onToggle: (id: number, active: boolean) => void
  onRunNow: (id: number) => void
  onEdit: (schedule: Schedule) => void
}

export function ScheduleList({ schedules, onDelete, onToggle, onRunNow, onEdit }: Props) {
  if (!schedules.length) return <p className="text-gray-500 py-8 text-center">No schedules yet</p>
  return (
    <div className="space-y-3">
      {schedules.map(s => (
        <div key={s.id} className="bg-gray-900 rounded-xl border border-gray-800 p-4 flex items-center gap-4">
          <div className="flex-1 min-w-0">
            <p className="font-medium text-white">{s.name}</p>
            <p className="text-xs text-gray-400 mt-0.5">
              {s.scraper_type} · {s.frequency} · {s.cron_expr || "on-demand"}
            </p>
            {s.last_run_at && (
              <p className="text-xs text-gray-500 mt-0.5">
                Last run: {format(new Date(s.last_run_at), "MMM d, HH:mm")}
              </p>
            )}
          </div>
          <StatusBadge status={s.is_active ? "active" : "inactive"} />
          <div className="flex gap-2">
            <button onClick={() => onRunNow(s.id)} className="px-2 py-1 text-xs bg-purple-700 hover:bg-purple-600 rounded transition-colors">
              Run Now
            </button>
            <button onClick={() => onEdit(s)} className="px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors">
              Edit
            </button>
            <button onClick={() => onToggle(s.id, !s.is_active)} className="px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors">
              {s.is_active ? "Pause" : "Resume"}
            </button>
            <button onClick={() => onDelete(s.id)} className="px-2 py-1 text-xs bg-red-900 hover:bg-red-800 rounded transition-colors">
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
