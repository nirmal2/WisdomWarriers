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
        {
          key: "resume_detected",
          label: "Recovery",
          render: r =>
            r.resume_detected ? (
              <span className="inline-flex items-center rounded-full border border-amber-700 bg-amber-900/40 px-2 py-0.5 text-xs font-medium text-amber-200">
                Resumed
              </span>
            ) : (
              <span className="text-xs text-gray-500">-</span>
            ),
        },
        { key: "status", label: "Status", render: r => <StatusBadge status={r.status} /> },
        {
          key: "apify_run",
          label: "Apify Run",
          render: r => r.apify_posts_run_id ?? r.apify_profiles_run_id ?? "-",
        },
        {
          key: "apify_dataset",
          label: "Dataset",
          render: r => r.apify_posts_dataset_id ?? r.apify_profiles_dataset_id ?? "-",
        },
        { key: "embedding_status", label: "Embeddings", render: r => <StatusBadge status={r.embedding_status} /> },
        { key: "items_fetched", label: "Items" },
        { key: "started_at", label: "Started", render: r => format(new Date(r.started_at), "MMM d, HH:mm") },
      ]}
      rows={runs}
    />
  )
}
