import { useState } from "react"
import { X } from "lucide-react"
import type { Schedule, ScheduleCreate } from "../../types/schedule"

interface Props {
  onSubmit: (data: ScheduleCreate) => void
  onClose: () => void
  initialData?: Schedule
}

export function ScheduleModal({ onSubmit, onClose, initialData }: Props) {
  const [form, setForm] = useState<ScheduleCreate>({
    name: initialData?.name ?? "",
    scraper_type: initialData?.scraper_type ?? "posts",
    frequency: initialData?.frequency ?? "daily",
    cron_expr: initialData?.cron_expr ?? "",
    results_limit: initialData?.results_limit ?? 50,
    only_posts_newer_than: initialData?.only_posts_newer_than ?? "",
    is_active: initialData?.is_active ?? true,
    batch_mode: initialData?.batch_mode ?? false,
  })

  function set<K extends keyof ScheduleCreate>(key: K, value: ScheduleCreate[K]) {
    setForm(f => ({ ...f, [key]: value }))
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    onSubmit({
      ...form,
      cron_expr: form.cron_expr || undefined,
      only_posts_newer_than: form.only_posts_newer_than || undefined,
    } as ScheduleCreate)
  }

  const fieldClass = "w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-500 outline-none focus:border-purple-500"
  const labelClass = "block text-xs font-medium text-gray-400 mb-1"

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-gray-900 rounded-2xl border border-gray-700 w-full max-w-lg p-6 shadow-2xl relative">
        <button onClick={onClose} className="absolute top-4 right-4 text-gray-500 hover:text-gray-200 transition-colors">
          <X size={18} />
        </button>
        <h2 className="text-base font-semibold text-gray-100 mb-5">{initialData ? "Edit Schedule" : "New Schedule"}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">

          <div>
            <label className={labelClass}>Name <span className="text-red-400">*</span></label>
            <input required className={fieldClass} value={form.name} onChange={e => set("name", e.target.value)} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelClass}>Scraper Type</label>
              <select className={fieldClass} value={form.scraper_type} onChange={e => set("scraper_type", e.target.value as "posts" | "profiles")}>
                <option value="posts">Posts</option>
                <option value="profiles">Profiles</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Frequency</label>
              <select className={fieldClass} value={form.frequency} onChange={e => set("frequency", e.target.value as ScheduleCreate["frequency"])}>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="on_demand">On Demand</option>
              </select>
            </div>
          </div>

          {form.frequency !== "on_demand" && (
            <div>
              <label className={labelClass}>Cron Expression <span className="text-gray-500 font-normal">(optional override)</span></label>
              <input className={fieldClass} placeholder="e.g. 0 9 * * 1" value={form.cron_expr ?? ""} onChange={e => set("cron_expr", e.target.value)} />
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelClass}>Results Limit</label>
              <input type="number" min={1} max={500} className={fieldClass} value={form.results_limit ?? 50} onChange={e => set("results_limit", Number(e.target.value))} />
            </div>
            {form.scraper_type === "posts" && (
              <div>
                <label className={labelClass}>Only Posts Newer Than</label>
                <input className={fieldClass} placeholder="e.g. 2024-01-01" value={form.only_posts_newer_than ?? ""} onChange={e => set("only_posts_newer_than", e.target.value)} />
              </div>
            )}
          </div>

          <div className="flex items-center gap-5 pt-1">
            <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer select-none">
              <input type="checkbox" checked={form.is_active} onChange={e => set("is_active", e.target.checked)} className="accent-purple-500 w-4 h-4" />
              Active
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer select-none">
              <input type="checkbox" checked={form.batch_mode} onChange={e => set("batch_mode", e.target.checked)} className="accent-purple-500 w-4 h-4" />
              Batch Mode
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm rounded-lg border border-gray-700 text-gray-300 hover:bg-gray-800 transition-colors">Cancel</button>
            <button type="submit" className="px-4 py-2 text-sm bg-purple-700 hover:bg-purple-600 rounded-lg text-white font-medium transition-colors">{initialData ? "Update" : "Save"}</button>
          </div>

        </form>
      </div>
    </div>
  )
}
