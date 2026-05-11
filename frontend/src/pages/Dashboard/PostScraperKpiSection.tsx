import { formatDistanceToNowStrict } from "date-fns"
import { KpiCard } from "../../components/KpiCard"
import { useScrapeRunSummary } from "../../hooks/useAnalytics"

interface PostScraperKpiSectionProps {
  maxRunId?: number
}

function formatStatus(status?: string) {
  if (!status) return "N/A"
  return status.charAt(0).toUpperCase() + status.slice(1)
}

function formatDuration(seconds: number) {
  if (!Number.isFinite(seconds) || seconds <= 0) return "-"
  const rounded = Math.round(seconds)
  if (rounded < 60) return `${rounded}s`
  const mins = Math.floor(rounded / 60)
  const secs = rounded % 60
  if (mins < 60) return `${mins}m ${secs}s`
  const hours = Math.floor(mins / 60)
  const remainingMins = mins % 60
  return `${hours}h ${remainingMins}m`
}

export function PostScraperKpiSection({ maxRunId }: PostScraperKpiSectionProps) {
  const { data } = useScrapeRunSummary(50, maxRunId)
  const postRuns = (data ?? []).filter(run => run.scraper_type === "posts")

  const latestRun = postRuns[0]
  const latestRunAge = latestRun?.started_at
    ? formatDistanceToNowStrict(new Date(latestRun.started_at), { addSuffix: true })
    : "N/A"

  const recentRuns = postRuns.slice(0, 10)
  const successfulRecentRuns = recentRuns.filter(run => run.status === "completed")
  const failedRecentRuns = recentRuns.filter(run => run.status === "failed")
  const successRate = recentRuns.length > 0
    ? `${Math.round((successfulRecentRuns.length / recentRuns.length) * 100)}%`
    : "0%"

  const completedRunsWithDuration = postRuns
    .filter(run => run.status === "completed" && typeof run.duration_seconds === "number" && run.duration_seconds > 0)
    .slice(0, 5)
  const avgDurationSeconds = completedRunsWithDuration.length > 0
    ? completedRunsWithDuration.reduce((sum, run) => sum + Number(run.duration_seconds ?? 0), 0) / completedRunsWithDuration.length
    : 0

  const latestCompletedRun = postRuns.find(run => run.status === "completed")

  return (
    <div className="space-y-3">
      <div>
        <h2 className="text-sm font-semibold text-gray-200">Post Scraper KPI</h2>
        <p className="text-xs text-gray-400 mt-1">Operational health metrics from recent post scraper runs.</p>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
        <KpiCard
          label="Latest Post Run"
          value={latestRun ? `#${latestRun.id}` : "N/A"}
          sub={latestRun ? `${formatStatus(latestRun.status)} • ${latestRunAge}` : "No post scraper runs"}
        />
        <KpiCard
          label="Latest Posts Fetched"
          value={latestRun ? Number(latestRun.items_fetched ?? 0).toLocaleString() : "0"}
          sub="From latest post scraper run"
        />
        <KpiCard
          label="Latest Profiles Requested"
          value={latestRun ? Number(latestRun.profiles_requested ?? 0).toLocaleString() : "0"}
          sub="Profiles submitted in latest run"
        />
        <KpiCard
          label="Success Rate (10 Runs)"
          value={successRate}
          sub={`${successfulRecentRuns.length}/${recentRuns.length || 0} runs completed`}
        />
        <KpiCard
          label="Failed Runs (10 Runs)"
          value={failedRecentRuns.length.toLocaleString()}
          sub="Recent post scraper failures"
        />
        <KpiCard
          label="Avg Duration (5 Success)"
          value={formatDuration(avgDurationSeconds)}
          sub={latestCompletedRun?.embedding_status ? `Last embedding: ${formatStatus(latestCompletedRun.embedding_status)}` : "No completed runs yet"}
        />
      </div>
    </div>
  )
}
