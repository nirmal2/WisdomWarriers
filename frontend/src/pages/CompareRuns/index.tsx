import { useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { DataTable } from "../../components/DataTable"
import { fetchRunComparison, fetchRuns } from "../../api/scrape"
import type { LatestPostDelta, ProfileDelta, ScrapeRun } from "../../types/schedule"

function fmtSigned(n: number) {
  return `${n >= 0 ? "+" : ""}${n.toLocaleString()}`
}

function fmtDate(value?: string) {
  if (!value) return "-"
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleString()
}

function toneClass(tone: "positive" | "negative" | "neutral") {
  if (tone === "positive") return "text-emerald-300"
  if (tone === "negative") return "text-rose-300"
  return "text-gray-300"
}

function deltaClass(value: number) {
  if (value > 0) return "text-emerald-300"
  if (value < 0) return "text-rose-300"
  return "text-gray-200"
}

export default function CompareRunsPage() {
  const [runAId, setRunAId] = useState<number | null>(null)
  const [runBId, setRunBId] = useState<number | null>(null)

  const { data: runsData, isLoading: runsLoading } = useQuery({
    queryKey: ["runs", "compare", "list"],
    queryFn: () => fetchRuns({ status: "completed", limit: 100 }),
  })

  const completedRuns = runsData?.items ?? []
  const effectiveRunAId = runAId
  const effectiveRunBId = runBId

  const { data: comparison, isLoading: compareLoading, error: compareError } = useQuery({
    queryKey: ["runs", "compare", effectiveRunAId, effectiveRunBId],
    queryFn: () => fetchRunComparison(effectiveRunAId as number, effectiveRunBId as number),
    enabled: !!effectiveRunAId && !!effectiveRunBId && effectiveRunAId !== effectiveRunBId,
  })

  const profileColumns = useMemo(
    () => [
      { key: "profile_id", label: "Profile ID", sortable: true },
      { key: "change_type", label: "Type", sortable: true },
      { key: "followers_run_a", label: "Followers A", sortable: true },
      { key: "followers_run_b", label: "Followers B", sortable: true },
      {
        key: "followers_delta",
        label: "Followers Delta",
        sortable: true,
        render: (row: ProfileDelta) => <span className={deltaClass(row.followers_delta)}>{fmtSigned(row.followers_delta)}</span>,
      },
      {
        key: "posts_delta",
        label: "Posts Delta",
        sortable: true,
        render: (row: ProfileDelta) => <span className={deltaClass(row.posts_delta)}>{fmtSigned(row.posts_delta)}</span>,
      },
    ],
    [],
  )

  const latestPostColumns = useMemo(
    () => [
      { key: "owner_username", label: "Owner", sortable: true },
      {
        key: "url",
        label: "Post",
        render: (row: LatestPostDelta) => (
          <a className="text-cyan-300 hover:underline" href={row.url} target="_blank" rel="noreferrer">
            Open
          </a>
        ),
      },
      { key: "change_type", label: "Type", sortable: true },
      {
        key: "likes_delta",
        label: "Likes Delta",
        sortable: true,
        render: (row: LatestPostDelta) => <span className={deltaClass(row.likes_delta)}>{fmtSigned(row.likes_delta)}</span>,
      },
      {
        key: "comments_delta",
        label: "Comments Delta",
        sortable: true,
        render: (row: LatestPostDelta) => <span className={deltaClass(row.comments_delta)}>{fmtSigned(row.comments_delta)}</span>,
      },
      {
        key: "views_delta",
        label: "Views Delta",
        sortable: true,
        render: (row: LatestPostDelta) => <span className={deltaClass(row.views_delta)}>{fmtSigned(row.views_delta)}</span>,
      },
    ],
    [],
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Compare Scrape Runs</h1>
        <p className="text-sm text-gray-400 mt-1">Pick two completed runs by date/time or run list, then compare profile and latest-post changes.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-3">
          <h2 className="text-sm font-semibold text-gray-200">Run A by Previous Scrape Date/Time</h2>
          <select
            value={runAId ?? ""}
            onChange={e => setRunAId(e.target.value ? Number(e.target.value) : null)}
            className="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm"
          >
            <option value="">Select run A</option>
            {completedRuns.map(run => (
              <option key={`a-${run.id}`} value={run.id}>
                #{run.id} - {fmtDate(run.finished_at)}
              </option>
            ))}
          </select>
          <p className="text-xs text-gray-400">Choose from completed scrape timestamps only.</p>
        </div>

        <div className="bg-gray-900 rounded-xl border border-gray-800 p-4 space-y-3">
          <h2 className="text-sm font-semibold text-gray-200">Run B by Previous Scrape Date/Time</h2>
          <select
            value={runBId ?? ""}
            onChange={e => setRunBId(e.target.value ? Number(e.target.value) : null)}
            className="w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm"
          >
            <option value="">Select run B</option>
            {completedRuns.map(run => (
              <option key={`b-${run.id}`} value={run.id}>
                #{run.id} - {fmtDate(run.finished_at)}
              </option>
            ))}
          </select>
          <p className="text-xs text-gray-400">Choose from completed scrape timestamps only.</p>
        </div>
      </div>

      <div className="bg-gray-900 rounded-xl border border-gray-800 p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-200">Select Runs From List</h2>
          <div className="text-xs text-gray-400">
            Effective pair: {effectiveRunAId ? `A=#${effectiveRunAId}` : "A=unset"} | {effectiveRunBId ? `B=#${effectiveRunBId}` : "B=unset"}
          </div>
        </div>

        {runsLoading ? (
          <p className="text-sm text-gray-400">Loading runs...</p>
        ) : (
          <DataTable
            rows={completedRuns}
            columns={[
              { key: "id", label: "Run", sortable: true },
              { key: "scraper_type", label: "Type", sortable: true },
              { key: "trigger", label: "Trigger", sortable: true },
              {
                key: "finished_at",
                label: "Finished",
                sortable: true,
                render: (row: ScrapeRun) => fmtDate(row.finished_at),
              },
              {
                key: "a",
                label: "Set A",
                render: (row: ScrapeRun) => (
                  <button
                    onClick={e => {
                      e.stopPropagation()
                      setRunAId(row.id)
                    }}
                    className="px-2 py-1 rounded-md bg-indigo-700 hover:bg-indigo-600 text-xs"
                  >
                    Run A
                  </button>
                ),
              },
              {
                key: "b",
                label: "Set B",
                render: (row: ScrapeRun) => (
                  <button
                    onClick={e => {
                      e.stopPropagation()
                      setRunBId(row.id)
                    }}
                    className="px-2 py-1 rounded-md bg-cyan-700 hover:bg-cyan-600 text-xs"
                  >
                    Run B
                  </button>
                ),
              },
            ]}
          />
        )}
      </div>

      {!!comparison && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <div className="rounded-lg border border-gray-800 bg-gray-900 p-3">
              <p className="text-xs text-gray-400">Common Profiles</p>
              <p className="text-lg font-semibold mt-1">{comparison.summary.common_profiles}</p>
            </div>
            <div className="rounded-lg border border-gray-800 bg-gray-900 p-3">
              <p className="text-xs text-gray-400">Net Followers Delta</p>
              <p className={`text-lg font-semibold mt-1 ${deltaClass(comparison.summary.net_followers_delta)}`}>{fmtSigned(comparison.summary.net_followers_delta)}</p>
            </div>
            <div className="rounded-lg border border-gray-800 bg-gray-900 p-3">
              <p className="text-xs text-gray-400">Common Latest Posts</p>
              <p className="text-lg font-semibold mt-1">{comparison.summary.common_latest_posts}</p>
            </div>
            <div className="rounded-lg border border-gray-800 bg-gray-900 p-3">
              <p className="text-xs text-gray-400">Net Likes Delta</p>
              <p className={`text-lg font-semibold mt-1 ${deltaClass(comparison.summary.net_likes_delta)}`}>{fmtSigned(comparison.summary.net_likes_delta)}</p>
            </div>
          </div>

          <div className="bg-gray-900 rounded-xl border border-gray-800 p-5 space-y-3">
            <h2 className="text-sm font-semibold text-gray-200">Insights</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {comparison.insights.map((insight, idx) => (
                <div key={`${insight.title}-${idx}`} className="rounded-lg border border-gray-800 bg-gray-950 p-3">
                  <p className="text-xs text-gray-400">{insight.title}</p>
                  <p className={`text-lg font-semibold mt-1 ${toneClass(insight.tone)}`}>{insight.value}</p>
                  <p className="text-xs text-gray-400 mt-1">{insight.detail}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-gray-900 rounded-xl border border-gray-800 p-5 space-y-3">
            <h2 className="text-sm font-semibold text-gray-200">Profile Deltas</h2>
            <DataTable rows={comparison.profile_deltas} columns={profileColumns} />
          </div>

          <div className="bg-gray-900 rounded-xl border border-gray-800 p-5 space-y-3">
            <h2 className="text-sm font-semibold text-gray-200">Latest Post Deltas</h2>
            <DataTable rows={comparison.latest_post_deltas} columns={latestPostColumns} />
          </div>
        </>
      )}

      {compareLoading && <p className="text-sm text-gray-400">Computing comparison...</p>}
      {compareError && <p className="text-sm text-rose-300">{(compareError as Error).message}</p>}
      {!!effectiveRunAId && !!effectiveRunBId && effectiveRunAId === effectiveRunBId && (
        <p className="text-sm text-amber-300">Choose two different runs.</p>
      )}
    </div>
  )
}
