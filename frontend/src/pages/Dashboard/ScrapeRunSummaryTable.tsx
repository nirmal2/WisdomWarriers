import { formatDistanceStrict } from "date-fns"
import { ChartCard } from "../../components/ChartCard"
import { DataTable } from "../../components/DataTable"
import { StatusBadge } from "../../components/StatusBadge"
import { useScrapeRunSummary } from "../../hooks/useAnalytics"
import type { ScrapeRunSummary } from "../../types/analytics"

const formatDuration = (durationSeconds: number | null) => {
  if (!durationSeconds || durationSeconds <= 0) return "-"
  return formatDistanceStrict(0, durationSeconds * 1000)
}

interface ScrapeRunSummaryTableProps {
  maxRunId?: number
}

export function ScrapeRunSummaryTable({ maxRunId }: ScrapeRunSummaryTableProps) {
  const { data } = useScrapeRunSummary(8, maxRunId)

  return (
    <ChartCard title="Scrape Run Summary">
      <p className="mb-4 text-xs text-gray-400">Latest runs enriched with schedule labels and execution duration.</p>
      <DataTable<ScrapeRunSummary>
        columns={[
          { key: "id", label: "#", sortable: true },
          { key: "scraper_type", label: "Type" },
          { key: "schedule_name", label: "Schedule", render: row => row.schedule_name ?? "Manual" },
          { key: "duration_seconds", label: "Duration", sortable: true, render: row => formatDuration(row.duration_seconds) },
          { key: "items_fetched", label: "Items", sortable: true },
          { key: "status", label: "Status", render: row => <StatusBadge status={row.status} /> },
        ]}
        rows={data ?? []}
      />
    </ChartCard>
  )
}