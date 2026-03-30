import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts"
import { ChartCard } from "../../components/ChartCard"
import { useHashtagFrequency } from "../../hooks/useAnalytics"

export function HashtagChart() {
  const { data } = useHashtagFrequency(20)
  return (
    <ChartCard title="Top Hashtags">
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data ?? []} layout="vertical">
          <XAxis type="number" tick={{ fill: "#9ca3af", fontSize: 11 }} />
          <YAxis dataKey="tag" type="category" width={120} tick={{ fill: "#9ca3af", fontSize: 11 }} />
          <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151" }} />
          <Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  )
}
