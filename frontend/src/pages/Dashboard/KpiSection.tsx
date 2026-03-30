import { useOverview } from "../../hooks/useAnalytics"
import { KpiCard } from "../../components/KpiCard"

export function KpiSection() {
  const { data } = useOverview()
  if (!data) return null
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <KpiCard label="Profiles" value={data.total_profiles.toLocaleString()} />
      <KpiCard label="Posts" value={data.total_posts.toLocaleString()} />
      <KpiCard label="Avg Followers" value={Math.round(data.avg_followers).toLocaleString()} />
      <KpiCard label="Top Profile" value={`@${data.top_profile}`} />
    </div>
  )
}
