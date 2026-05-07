import { BarChart, Bar, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { ChartCard } from "../../components/ChartCard"
import { useHashtagPerformance } from "../../hooks/useAnalytics"

interface HashtagPerformanceCardProps {
  periodLabel?: string
}

export function HashtagPerformanceCard({ periodLabel }: HashtagPerformanceCardProps) {
  const { data } = useHashtagPerformance(periodLabel, undefined, 12)

  return (
    <ChartCard title="Hashtag Performance">
      <p className="mb-4 text-xs text-gray-400">Top hashtags ranked by engagement rate in the latest materialized snapshot.</p>
      <ResponsiveContainer width="100%" height={360}>
        <BarChart data={data ?? []} layout="vertical" margin={{ left: 12, right: 12 }}>
          <CartesianGrid stroke="#1f2937" horizontal={false} />
          <XAxis type="number" tick={{ fill: "#9ca3af", fontSize: 11 }} unit="%" />
          <YAxis dataKey="tag" type="category" width={120} tick={{ fill: "#9ca3af", fontSize: 11 }} />
          <Tooltip
            contentStyle={{ background: "#111827", border: "1px solid #374151" }}
            formatter={value => `${Number(value ?? 0).toFixed(2)}%`}
            labelFormatter={value => `#${String(value ?? "")}`}
          />
          <Bar dataKey="avg_engagement_rate" fill="#8b5cf6" radius={[0, 6, 6, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  )
}