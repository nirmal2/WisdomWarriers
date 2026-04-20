import { BarChart, Bar, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { ChartCard } from "../../components/ChartCard"
import { useGradeBenchmarks } from "../../hooks/useAnalytics"

export function GradeBenchmarksChart() {
  const { data } = useGradeBenchmarks()
  const chartData = (data ?? []).map(item => ({
    ...item,
    label: item.category ? `${item.grade} · ${item.category}` : item.grade,
  }))

  return (
    <ChartCard title="Grade Benchmarks">
      <p className="mb-4 text-xs text-gray-400">Average engagement rate by scrape grade for the latest tracked period.</p>
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 16, right: 16 }}>
          <CartesianGrid stroke="#1f2937" horizontal={false} />
          <XAxis type="number" tick={{ fill: "#9ca3af", fontSize: 11 }} unit="%" />
          <YAxis dataKey="label" type="category" width={120} tick={{ fill: "#9ca3af", fontSize: 11 }} />
          <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151" }} formatter={value => `${Number(value ?? 0).toFixed(2)}%`} />
          <Bar dataKey="avg_engagement_rate" fill="#f59e0b" radius={[0, 6, 6, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  )
}