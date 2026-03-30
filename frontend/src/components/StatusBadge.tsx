import clsx from "clsx"

type Status = "completed" | "running" | "failed" | "pending" | "skipped" | "not_started" | string

const colors: Record<string, string> = {
  completed: "bg-green-900 text-green-300",
  running: "bg-blue-900 text-blue-300",
  failed: "bg-red-900 text-red-300",
  pending: "bg-amber-900 text-amber-300",
  skipped: "bg-gray-700 text-gray-200",
  not_started: "bg-slate-700 text-slate-200",
  active: "bg-green-900 text-green-300",
  inactive: "bg-gray-700 text-gray-300",
}

export function StatusBadge({ status }: { status: Status }) {
  return (
    <span className={clsx("text-xs font-medium px-2 py-0.5 rounded-full", colors[status] ?? "bg-gray-700 text-gray-300")}>
      {status}
    </span>
  )
}
