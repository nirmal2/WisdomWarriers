import { useQuery } from "@tanstack/react-query"
import { fetchRuns } from "../../api/scrape"
import { DataTable } from "../../components/DataTable"
import { StatusBadge } from "../../components/StatusBadge"
import type { ScrapeRun } from "../../types/schedule"
import { format } from "date-fns"

export function RecentRunsTable() {
  const { data } = useQuery({ queryKey: ["runs"], queryFn: () => fetchRuns({ limit: 10 }) })
  const runs = data?.items ?? []

  return (
    <DataTable<ScrapeRun>
      columns={[
        { key: "id", label: "#" },
        { key: "scraper_type", label: "Type" },
        { key: "trigger", label: "Trigger" },
        { key: "status", label: "Status", render: r => <StatusBadge status={r.status} /> },
        { key: "embedding_status", label: "Embeddings", render: r => <StatusBadge status={r.embedding_status} /> },
        { key: "items_fetched", label: "Items" },
        { key: "started_at", label: "Started", render: r => format(new Date(r.started_at), "MMM d, HH:mm") },
      ]}
      rows={runs}
    />
  )
}
