import { useTopProfiles } from "../../hooks/useAnalytics"

const MEDALS = ["🥇", "🥈", "🥉"]

export function TopProfilesTable() {
  const { data, isLoading } = useTopProfiles("followers_count", 10)

  if (isLoading) {
    return (
      <div className="h-64 animate-pulse rounded-3xl border border-black/5 bg-white shadow-md" />
    )
  }

  const profiles = data ?? []
  const max = profiles[0]?.value ?? 1

  return (
    <section className="overflow-hidden rounded-3xl bg-white text-slate-900 shadow-md ring-1 ring-black/5">
      <div className="bg-gradient-to-br from-indigo-500 to-violet-600 px-5 py-4 text-white">
        <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-white/70">Leaderboard</p>
        <h2 className="mt-1 text-lg font-bold">Top 10 Profiles</h2>
        <p className="mt-1 text-sm text-white/80">Ranked by follower count</p>
      </div>

      <ol className="space-y-3 px-5 py-4">
        {profiles.map((p, i) => {
          const pct = Math.round((p.value / max) * 100)
          return (
            <li key={p.username} className="flex items-center gap-3 rounded-2xl bg-slate-50 px-3 py-3 ring-1 ring-slate-100">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 text-sm font-bold text-white shadow-sm">
                {i < 3 ? MEDALS[i] : i + 1}
              </span>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="truncate text-sm font-semibold text-slate-800">@{p.username}</span>
                  <span className="ml-2 shrink-0 text-xs font-semibold text-violet-600">
                    {p.value.toLocaleString()}
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-200">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-600 transition-all duration-500"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            </li>
          )
        })}
      </ol>
    </section>
  )
}
