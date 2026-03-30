import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts"
import { ChartCard } from "../../components/ChartCard"
import { useFollowerGrowth } from "../../hooks/useAnalytics"

export function FollowerGrowthChart() {
  const { data } = useFollowerGrowth()
  return (
    <ChartCard title="Total Follower Growth">
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={data ?? []}>
          <XAxis dataKey="period_label" tick={{ fill: "#9ca3af", fontSize: 11 }} />
          <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} />
          <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151" }} />
          <Line type="monotone" dataKey="followers_count" stroke="#60a5fa" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  )
}
