import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts"
import { ChartCard } from "../../components/ChartCard"
import { usePostVolume } from "../../hooks/useAnalytics"

export function PostVolumeChart() {
  const { data } = usePostVolume()
  return (
    <ChartCard title="Posts Per Period">
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data ?? []}>
          <XAxis dataKey="period_label" tick={{ fill: "#9ca3af", fontSize: 11 }} />
          <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} />
          <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151" }} />
          <Bar dataKey="post_count" fill="#34d399" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  )
}
