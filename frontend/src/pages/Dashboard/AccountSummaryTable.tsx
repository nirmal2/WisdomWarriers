import { ChartCard } from "../../components/ChartCard"
import { DataTable } from "../../components/DataTable"
import { useAccountSummary } from "../../hooks/useAnalytics"
import type { AccountSummary } from "../../types/analytics"

export function AccountSummaryTable() {
  const { data, isLoading } = useAccountSummary(undefined, 10)
  const rows = data ?? []

  return (
    <ChartCard title="Account Monthly Summary">
      <p className="mb-4 text-xs text-gray-400">
        Latest period: <span className="text-gray-200">{rows[0]?.period_label ?? "No data"}</span>
      </p>
      {isLoading ? (
        <div className="h-80 animate-pulse rounded-xl bg-gray-800/60" />
      ) : (
        <DataTable<AccountSummary>
          columns={[
            { key: "owner_username", label: "Account", render: row => `@${row.owner_username}` },
            { key: "grade", label: "Grade" },
            { key: "posts_count", label: "Posts", sortable: true },
            { key: "avg_engagement_rate", label: "Avg ER", sortable: true, render: row => `${Number(row.avg_engagement_rate ?? 0).toFixed(2)}%` },
            { key: "avg_likes", label: "Avg Likes", sortable: true, render: row => Number(row.avg_likes ?? 0).toLocaleString() },
            { key: "peak_engagement_rate", label: "Peak ER", sortable: true, render: row => `${Number(row.peak_engagement_rate ?? 0).toFixed(2)}%` },
            { key: "most_active_day", label: "Best Day" },
          ]}
          rows={rows}
        />
      )}
    </ChartCard>
  )
}