import { useOverview } from "../../hooks/useAnalytics"
import { KpiCard } from "../../components/KpiCard"

interface KpiSectionProps {
  periodLabel?: string
}

export function KpiSection({ periodLabel }: KpiSectionProps) {
  const { data } = useOverview(periodLabel)
  if (!data) return null
  return (
    <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
      <KpiCard label="Profiles" value={data.total_profiles.toLocaleString()} />
      <KpiCard label="Posts" value={data.total_posts.toLocaleString()} />
      <KpiCard label="Avg Followers" value={Math.round(data.avg_followers).toLocaleString()} />
      <KpiCard label="Top Profile" value={`@${data.top_profile}`} />
      <KpiCard label="Active Accounts" value={data.active_accounts.toLocaleString()} sub={data.latest_period ?? "No period"} />
      <KpiCard label="Avg Engagement" value={`${Number(data.avg_engagement_rate ?? 0).toFixed(2)}%`} sub={data.top_hashtag ? `Top tag: #${data.top_hashtag}` : "No hashtag data"} />
    </div>
  )
}
