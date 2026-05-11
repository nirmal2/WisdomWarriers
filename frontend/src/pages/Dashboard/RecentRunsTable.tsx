import { useQuery } from "@tanstack/react-query"
import { fetchRuns } from "../../api/scrape"
import { DataTable } from "../../components/DataTable"
import { StatusBadge } from "../../components/StatusBadge"
import type { ScrapeRun } from "../../types/schedule"
import { format } from "date-fns"

interface RecentRunsTableProps {
  onSelectRun?: (run: ScrapeRun) => void
  onRefetchStage?: (run: ScrapeRun, stage: "posts" | "profiles") => void
  refetchingRunId?: number | null
  refetchingStage?: "posts" | "profiles" | null
}

export function RecentRunsTable({ onSelectRun, onRefetchStage, refetchingRunId = null, refetchingStage = null }: RecentRunsTableProps) {
  const { data } = useQuery({ queryKey: ["runs"], queryFn: () => fetchRuns({ limit: 10 }) })
  const runs = data?.items ?? []

  const getRefetchBlockReason = (run: ScrapeRun, stage: "posts" | "profiles"): string | null => {
    if (run.status === "running") return "Run is currently running"
    if (refetchingRunId === run.id && refetchingStage !== null) return "A refetch is already in progress for this run"

    if (stage === "posts") {
      if (!run.apify_posts_run_id || !run.apify_posts_dataset_id) {
        return "No stored Apify posts run/dataset metadata for this run"
      }
      return null
    }

    if (!run.apify_profiles_run_id || !run.apify_profiles_dataset_id) {
      return "No stored Apify profiles run/dataset metadata for this run"
    }
    return null
  }

  return (
    <DataTable<ScrapeRun>
      columns={[
        { key: "id", label: "#" },
        { key: "scraper_type", label: "Type" },
        { key: "trigger", label: "Trigger" },
        {
          key: "resume_detected",
          label: "Recovery",
          render: (r: ScrapeRun) =>
            r.resume_detected ? (
              <span className="inline-flex items-center rounded-full border border-amber-700 bg-amber-900/40 px-2 py-0.5 text-xs font-medium text-amber-200">
                Resumed
              </span>
            ) : (
              <span className="text-xs text-gray-500">-</span>
            ),
        },
        { key: "status", label: "Status", render: (r: ScrapeRun) => <StatusBadge status={r.status} /> },
        {
          key: "apify_run",
          label: "Apify Run",
          render: (r: ScrapeRun) => r.apify_posts_run_id ?? r.apify_profiles_run_id ?? "-",
        },
        {
          key: "apify_dataset",
          label: "Dataset",
          render: (r: ScrapeRun) => r.apify_posts_dataset_id ?? r.apify_profiles_dataset_id ?? "-",
        },
        onRefetchStage
          ? {
              key: "actions",
              label: "Actions",
              render: (r: ScrapeRun) => (
                <div className="flex flex-wrap gap-2">
                  {(() => {
                    const postsBlockReason = getRefetchBlockReason(r, "posts")
                    const profilesBlockReason = getRefetchBlockReason(r, "profiles")
                    return (
                      <>
                  <button
                    type="button"
                    onClick={() => {
                      onSelectRun?.(r)
                      onRefetchStage(r, "posts")
                    }}
                    disabled={Boolean(postsBlockReason)}
                    title={postsBlockReason ?? "Refetch Posts stage from Apify"}
                    className="rounded-md bg-blue-600 px-2 py-1 text-[11px] font-semibold text-white transition-colors hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {refetchingRunId === r.id && refetchingStage === "posts" ? "Refetching…" : "Refetch Posts"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      onSelectRun?.(r)
                      onRefetchStage(r, "profiles")
                    }}
                    disabled={Boolean(profilesBlockReason)}
                    title={profilesBlockReason ?? "Refetch Profiles stage from Apify"}
                    className="rounded-md bg-fuchsia-600 px-2 py-1 text-[11px] font-semibold text-white transition-colors hover:bg-fuchsia-500 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {refetchingRunId === r.id && refetchingStage === "profiles" ? "Refetching…" : "Refetch Profiles"}
                  </button>
                        {(postsBlockReason || profilesBlockReason) && (
                          <p className="w-full rounded-sm border border-slate-700/70 bg-slate-900/70 px-1.5 py-1 text-[10px] text-slate-300">
                            {postsBlockReason && !profilesBlockReason
                              ? `Posts: ${postsBlockReason}`
                              : profilesBlockReason && !postsBlockReason
                                ? `Profiles: ${profilesBlockReason}`
                                : postsBlockReason === profilesBlockReason
                                  ? postsBlockReason
                                  : `Posts: ${postsBlockReason} | Profiles: ${profilesBlockReason}`}
                          </p>
                        )}
                      </>
                    )
                  })()}
                </div>
              ),
            }
          : null,
        { key: "embedding_status", label: "Embeddings", render: (r: ScrapeRun) => <StatusBadge status={r.embedding_status} /> },
        { key: "items_fetched", label: "Items" },
        { key: "started_at", label: "Started", render: (r: ScrapeRun) => format(new Date(r.started_at), "MMM d, HH:mm") },
      ].filter(Boolean) as Array<{
        key: keyof ScrapeRun | string
        label: string
        render?: (row: ScrapeRun) => React.ReactNode
      }>}
      rows={runs}
    />
  )
}
