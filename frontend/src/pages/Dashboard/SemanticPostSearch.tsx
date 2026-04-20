import { useEffect, useMemo, useState } from "react"
import { LineChart, Line, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { Search } from "lucide-react"
import { ChartCard } from "../../components/ChartCard"
import { usePostEngagementHistory, useSemanticPostSearch } from "../../hooks/useAnalytics"

const truncate = (value: string | null | undefined, max = 120) => {
  if (!value) return "No caption"
  return value.length > max ? `${value.slice(0, max)}...` : value
}

export function SemanticPostSearch() {
  const [query, setQuery] = useState("")
  const [username, setUsername] = useState("")
  const [submittedQuery, setSubmittedQuery] = useState("")
  const [submittedUsername, setSubmittedUsername] = useState("")
  const [selectedShortCode, setSelectedShortCode] = useState<string | undefined>()

  const search = useSemanticPostSearch(submittedQuery, submittedUsername || undefined, 6)
  const results = search.data ?? []

  useEffect(() => {
    if (results.length > 0) {
      setSelectedShortCode(results[0].short_code)
      return
    }
    setSelectedShortCode(undefined)
  }, [results])

  const history = usePostEngagementHistory(selectedShortCode)
  const historySeries = useMemo(() => (history.data ?? []).map(point => ({
    ...point,
    label: point.period_label,
  })), [history.data])

  return (
    <ChartCard title="Semantic Post Search">
      <div className="mb-4 flex flex-col gap-3 md:flex-row">
        <label className="flex-1">
          <span className="mb-1 block text-xs uppercase tracking-wide text-gray-500">Query</span>
          <input
            value={query}
            onChange={event => setQuery(event.target.value)}
            placeholder="Find posts about meditation retreats, reels, or campaigns"
            className="w-full rounded-xl border border-gray-700 bg-gray-950 px-4 py-3 text-sm text-gray-100 outline-none transition focus:border-blue-400"
          />
        </label>
        <label className="md:w-52">
          <span className="mb-1 block text-xs uppercase tracking-wide text-gray-500">Username</span>
          <input
            value={username}
            onChange={event => setUsername(event.target.value)}
            placeholder="Optional @username"
            className="w-full rounded-xl border border-gray-700 bg-gray-950 px-4 py-3 text-sm text-gray-100 outline-none transition focus:border-blue-400"
          />
        </label>
        <div className="flex items-end">
          <button
            type="button"
            onClick={() => {
              setSubmittedQuery(query.trim())
              setSubmittedUsername(username.trim().replace(/^@/, ""))
            }}
            className="inline-flex items-center gap-2 rounded-xl bg-blue-500 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-400 disabled:cursor-not-allowed disabled:bg-gray-700"
            disabled={query.trim().length < 2}
          >
            <Search size={16} />
            Search posts
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <div className="space-y-3">
          <p className="text-xs text-gray-400">Searches the pgvector-backed post index and returns the closest matching posts by caption and embedding similarity.</p>
          {search.isFetching && <div className="h-28 animate-pulse rounded-xl bg-gray-800/60" />}
          {!search.isFetching && submittedQuery && results.length === 0 && (
            <div className="rounded-xl border border-dashed border-gray-700 px-4 py-6 text-sm text-gray-400">No matching posts found.</div>
          )}
          {results.map(result => {
            const selected = result.short_code === selectedShortCode
            return (
              <button
                key={result.id}
                type="button"
                onClick={() => setSelectedShortCode(result.short_code)}
                className={`w-full rounded-2xl border p-3 text-left transition ${selected ? "border-blue-400 bg-blue-500/10" : "border-gray-800 bg-gray-950 hover:border-gray-700"}`}
              >
                <div className="flex gap-3">
                  {result.display_url ? (
                    <img src={result.display_url} alt={result.short_code} className="h-16 w-16 rounded-xl object-cover" />
                  ) : (
                    <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-gray-800 text-xs text-gray-400">No image</div>
                  )}
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <p className="truncate text-sm font-semibold text-white">@{result.owner_username}</p>
                      <p className="text-xs font-medium text-blue-300">{(Number(result.similarity) * 100).toFixed(1)}% match</p>
                    </div>
                    <p className="mt-1 text-xs text-gray-400">{truncate(result.caption)}</p>
                    <div className="mt-2 flex gap-4 text-xs text-gray-300">
                      <span>{Number(result.likes_count ?? 0).toLocaleString()} likes</span>
                      <span>{Number(result.engagement_rate ?? 0).toFixed(2)}% ER</span>
                    </div>
                  </div>
                </div>
              </button>
            )
          })}
        </div>

        <div>
          <p className="mb-3 text-xs text-gray-400">Post engagement history for the selected search result.</p>
          {selectedShortCode && historySeries.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={historySeries}>
                <CartesianGrid stroke="#1f2937" />
                <XAxis dataKey="label" tick={{ fill: "#9ca3af", fontSize: 11 }} />
                <YAxis yAxisId="left" tick={{ fill: "#9ca3af", fontSize: 11 }} />
                <YAxis yAxisId="right" orientation="right" tick={{ fill: "#9ca3af", fontSize: 11 }} />
                <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151" }} />
                <Line yAxisId="left" type="monotone" dataKey="likes_count" stroke="#f472b6" strokeWidth={2} dot />
                <Line yAxisId="right" type="monotone" dataKey="likes_rate" stroke="#60a5fa" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-[320px] items-center justify-center rounded-xl border border-dashed border-gray-700 text-sm text-gray-400">
              {submittedQuery ? "Select a result with history to inspect trend data." : "Run a search to inspect engagement history."}
            </div>
          )}
        </div>
      </div>
    </ChartCard>
  )
}