import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts"
import { ChartCard } from "../../components/ChartCard"
import { useEngagement } from "../../hooks/useAnalytics"

export function EngagementChart() {
  const { data } = useEngagement()
  const top = (data ?? []).slice(0, 10)
  return (
    <ChartCard title="Avg Likes & Plays by Profile">
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={top} layout="vertical">
          <XAxis type="number" tick={{ fill: "#9ca3af", fontSize: 11 }} />
          <YAxis dataKey="owner_username" type="category" width={130} tick={{ fill: "#9ca3af", fontSize: 11 }} />
          <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151" }} />
          <Legend />
          <Bar dataKey="avg_likes" fill="#f472b6" radius={[0, 4, 4, 0]} name="Avg Likes" />
          <Bar dataKey="avg_plays" fill="#fb923c" radius={[0, 4, 4, 0]} name="Avg Plays" />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  )
}
