import { Fragment } from "react"

import { ChartCard } from "../../components/ChartCard"
import { usePostingTimeHeatmap } from "../../hooks/useAnalytics"

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

const formatHour = (hour: number) => `${String(hour).padStart(2, "0")}:00`

export function PostingTimeHeatmap() {
interface PostingTimeHeatmapProps {
  periodLabel?: string
}

export function PostingTimeHeatmap({ periodLabel }: PostingTimeHeatmapProps) {
  const { data } = usePostingTimeHeatmap(undefined, periodLabel)
  const cells = data ?? []
  const maxEngagement = Math.max(...cells.map(cell => Number(cell.avg_engagement_rate ?? 0)), 0)

  return (
    <ChartCard title="Posting Time Heatmap">
      <p className="mb-4 text-xs text-gray-400">Average engagement by day and hour across the latest posting-time materialized view.</p>
      <div className="overflow-x-auto">
        <div className="min-w-[980px]">
          <div className="grid" style={{ gridTemplateColumns: "80px repeat(24, minmax(0, 1fr))" }}>
            <div className="p-2 text-xs text-gray-500">Day / Hour</div>
            {Array.from({ length: 24 }, (_, hour) => (
              <div key={hour} className="p-2 text-center text-[11px] text-gray-500">{formatHour(hour)}</div>
            ))}

            {DAYS.map((day, dayIndex) => (
              <Fragment key={day}>
                <div key={`${day}-label`} className="p-2 text-sm font-medium text-gray-300">{day}</div>
                {Array.from({ length: 24 }, (_, hour) => {
                  const cell = cells.find(item => item.day_of_week === dayIndex && item.hour_of_day === hour)
                  const engagement = Number(cell?.avg_engagement_rate ?? 0)
                  const intensity = maxEngagement > 0 ? engagement / maxEngagement : 0
                  return (
                    <div
                      key={`${day}-${hour}`}
                      className="m-1 rounded-lg border border-white/5 p-2 text-center text-[11px] text-gray-100"
                      style={{ backgroundColor: `rgba(96, 165, 250, ${0.08 + intensity * 0.72})` }}
                      title={cell ? `${day} ${formatHour(hour)} • ER ${engagement.toFixed(2)}% • ${cell.post_count} posts` : `${day} ${formatHour(hour)} • No data`}
                    >
                      <div className="font-semibold">{cell ? `${engagement.toFixed(1)}%` : "-"}</div>
                      <div className="text-[10px] text-gray-200/80">{cell ? `${cell.post_count} posts` : ""}</div>
                    </div>
                  )
                })}
              </Fragment>
            ))}
          </div>
        </div>
      </div>
    </ChartCard>
  )
}