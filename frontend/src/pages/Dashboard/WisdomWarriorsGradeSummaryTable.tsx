import { useMemo } from "react"
import { ChartCard } from "../../components/ChartCard"
import { useWisdomWarriors, useWisdomWarriorsMonthlyViews } from "../../hooks/useWisdomWarriors"
import type { InfluencerGrade } from "../../types/wisdomWarrior"

interface WisdomWarriorsGradeSummaryTableProps {
  selectedSnapshotRunId?: number
  monthLabel?: string
}

type GradeSummary = {
  grade: InfluencerGrade
  count: number
  totalViews: number
  topChannels: { username: string; views: number }[]
}

const GRADE_ORDER: InfluencerGrade[] = ["A", "B", "C", "D", "E", "Inactive"]

function formatViewCount(value: number) {
  return Math.round(value).toLocaleString()
}

export function WisdomWarriorsGradeSummaryTable({ selectedSnapshotRunId, monthLabel }: WisdomWarriorsGradeSummaryTableProps) {
  const { data: warriors = [], isLoading: isLoadingWarriors } = useWisdomWarriors()
  const { data: monthlyViews = [], isLoading: isLoadingViews } = useWisdomWarriorsMonthlyViews({
    month: monthLabel ?? "",
    applyFilters: false,
    snapshotRunId: selectedSnapshotRunId,
  })

  const gradeSummaries = useMemo<GradeSummary[]>(() => {
    const viewsByUsername = new Map(
      monthlyViews.map(item => [item.username.trim().toLowerCase(), Number(item.total_views ?? 0)])
    )

    return GRADE_ORDER.map(grade => {
      const gradeWarriors = warriors.filter(warrior => warrior.grade === grade)
      const topChannels = gradeWarriors
        .map(warrior => ({
          username: warrior.username,
          views: viewsByUsername.get(warrior.username.trim().toLowerCase()) ?? 0,
        }))
        .filter(channel => channel.views > 0)
        .sort((a, b) => b.views - a.views || a.username.localeCompare(b.username))
        .slice(0, 10)

      const totalViews = gradeWarriors.reduce(
        (sum, warrior) => sum + (viewsByUsername.get(warrior.username.trim().toLowerCase()) ?? 0),
        0
      )

      return {
        grade,
        count: gradeWarriors.length,
        totalViews,
        topChannels,
      }
    })
  }, [monthlyViews, warriors])

  const isLoading = isLoadingWarriors || isLoadingViews

  return (
    <ChartCard title="Wisdom Warriors Grade Summary">
      <p className="mb-4 text-xs text-gray-400">
        Grade-wise count of Wisdom Warriors, top 10 channels by views, and total views for {monthLabel ?? "current month"}.
      </p>
      <p className="mb-4 text-[11px] text-gray-500">
        Data source: post_snapshot (run_id: {selectedSnapshotRunId ?? "N/A"})
      </p>

      {isLoading ? (
        <div className="h-64 animate-pulse rounded-xl bg-gray-800/60" />
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-[900px] w-full border border-gray-700 text-sm">
            <thead>
              <tr className="bg-gray-800/80 text-red-400">
                {gradeSummaries.map(summary => (
                  <th key={summary.grade} className="border border-gray-700 px-3 py-2 text-left font-semibold">
                    Grade {summary.grade}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr className="bg-gray-900/80 align-top text-red-300">
                {gradeSummaries.map(summary => (
                  <td key={summary.grade} className="border border-gray-700 px-3 py-2">
                    <p className="font-semibold">Number of Grade {summary.grade} WWs</p>
                    <p className="mt-1 text-white">{summary.count.toLocaleString()}</p>
                  </td>
                ))}
              </tr>
              <tr className="bg-gray-800/40 align-top text-red-300">
                {gradeSummaries.map(summary => (
                  <td key={summary.grade} className="border border-gray-700 px-3 py-2">
                    <p className="font-semibold">Top 10 channels (wrt views)</p>
                    {summary.topChannels.length === 0 ? (
                      <p className="mt-1 text-gray-400">No channels</p>
                    ) : (
                      <ol className="mt-1 space-y-1 text-xs text-gray-100">
                        {summary.topChannels.map(channel => (
                          <li key={`${summary.grade}-${channel.username}`}>
                            @{channel.username} ({formatViewCount(channel.views)})
                          </li>
                        ))}
                      </ol>
                    )}
                  </td>
                ))}
              </tr>
              <tr className="bg-gray-900/80 text-red-300">
                {gradeSummaries.map(summary => (
                  <td key={summary.grade} className="border border-gray-700 px-3 py-2">
                    <p className="font-semibold">Total Views</p>
                    <p className="mt-1 text-white">{formatViewCount(summary.totalViews)}</p>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </ChartCard>
  )
}