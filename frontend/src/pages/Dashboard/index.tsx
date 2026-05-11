import { useEffect, useMemo, useState } from "react"
import { KpiSection } from "./KpiSection"
import { TopProfilesTable } from "./TopProfilesTable"
import { AccountSummaryTable } from "./AccountSummaryTable"
import { GradeBenchmarksChart } from "./GradeBenchmarksChart"
import { HashtagPerformanceCard } from "./HashtagPerformanceCard"
import { PostingTimeHeatmap } from "./PostingTimeHeatmap"
import { ScrapeRunSummaryTable } from "./ScrapeRunSummaryTable"
import { SemanticPostSearch } from "./SemanticPostSearch"
import { WisdomWarriorsGradeSummaryTable } from "./WisdomWarriorsGradeSummaryTable"
import { PostScraperKpiSection } from "./PostScraperKpiSection"
import { FollowerGrowthChart } from "../Analytics/FollowerGrowthChart"
import { PostVolumeChart } from "../Analytics/PostVolumeChart"

interface DashboardProps {
  selectedSnapshotRunId?: number
  selectedScrapedAt?: string
  selectedMonth?: string
}

type WidgetKey =
  | "kpiSection"
  | "postScraperKpis"
  | "followerGrowth"
  | "postVolume"
  | "topProfiles"
  | "accountSummary"
  | "gradeBenchmarks"
  | "hashtagPerformance"
  | "postingTimeHeatmap"
  | "scrapeRunSummary"
  | "semanticPostSearch"

type WidgetPrefs = Record<WidgetKey, boolean>

const DASHBOARD_WIDGET_PREFS_KEY = "dashboard-widget-prefs-v1"

const WIDGETS: Array<{ key: WidgetKey; label: string }> = [
  { key: "kpiSection", label: "KPI Section" },
  { key: "postScraperKpis", label: "Post Scraper KPI" },
  { key: "followerGrowth", label: "Follower Growth" },
  { key: "postVolume", label: "Post Volume" },
  { key: "topProfiles", label: "Top Profiles" },
  { key: "accountSummary", label: "Account Summary" },
  { key: "gradeBenchmarks", label: "Grade Benchmarks" },
  { key: "hashtagPerformance", label: "Hashtag Performance" },
  { key: "postingTimeHeatmap", label: "Posting Time Heatmap" },
  { key: "scrapeRunSummary", label: "Scrape Run Summary" },
  { key: "semanticPostSearch", label: "Semantic Post Search" },
]

const DEFAULT_WIDGET_PREFS: WidgetPrefs = {
  kpiSection: true,
  postScraperKpis: true,
  followerGrowth: true,
  postVolume: true,
  topProfiles: true,
  accountSummary: true,
  gradeBenchmarks: true,
  hashtagPerformance: true,
  postingTimeHeatmap: true,
  scrapeRunSummary: true,
  semanticPostSearch: true,
}

const readWidgetPrefs = (): WidgetPrefs => {
  if (typeof window === "undefined") return DEFAULT_WIDGET_PREFS
  try {
    const raw = window.localStorage.getItem(DASHBOARD_WIDGET_PREFS_KEY)
    if (!raw) return DEFAULT_WIDGET_PREFS
    const parsed = JSON.parse(raw) as Partial<WidgetPrefs>
    return {
      ...DEFAULT_WIDGET_PREFS,
      ...parsed,
    }
  } catch {
    return DEFAULT_WIDGET_PREFS
  }
}

const toPeriodLabel = (scrapedAt?: string): string | undefined => {
  if (!scrapedAt) return undefined
  const date = new Date(scrapedAt)
  if (Number.isNaN(date.getTime())) return undefined
  return date.toISOString().slice(0, 7)
}

export default function Dashboard({ selectedSnapshotRunId, selectedScrapedAt, selectedMonth }: DashboardProps) {
  const periodLabel = selectedMonth || toPeriodLabel(selectedScrapedAt)
  const [widgetPrefs, setWidgetPrefs] = useState<WidgetPrefs>(readWidgetPrefs)

  useEffect(() => {
    window.localStorage.setItem(DASHBOARD_WIDGET_PREFS_KEY, JSON.stringify(widgetPrefs))
  }, [widgetPrefs])

  const widgetToggleItems = useMemo(() => WIDGETS, [])

  const isOn = (key: WidgetKey) => widgetPrefs[key]

  const showTrends = isOn("followerGrowth") || isOn("postVolume")
  const showTopProfiles = isOn("topProfiles")
  const showAccountBenchmarks = isOn("accountSummary") || isOn("gradeBenchmarks")
  const showHashtagHeatmap = isOn("hashtagPerformance") || isOn("postingTimeHeatmap")
  const showRunAndSemantic = isOn("scrapeRunSummary") || isOn("semanticPostSearch")

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-sm text-gray-400 mt-1">View-backed analytics across account performance, hashtag lift, posting times, run health, and semantic post discovery.</p>
      </div>
      <WisdomWarriorsGradeSummaryTable
        selectedSnapshotRunId={selectedSnapshotRunId}
        monthLabel={periodLabel}
      />
      <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-gray-400">Widget Visibility</p>
        <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {widgetToggleItems.map(item => (
            <label key={item.key} className="flex items-center justify-between rounded-lg border border-gray-800 bg-gray-950/60 px-3 py-2 text-sm text-gray-200">
              <span>{item.label}</span>
              <button
                type="button"
                onClick={() => setWidgetPrefs(prev => ({ ...prev, [item.key]: !prev[item.key] }))}
                className={isOn(item.key) ? "rounded bg-emerald-700 px-2 py-1 text-[11px] font-semibold text-emerald-100" : "rounded bg-gray-700 px-2 py-1 text-[11px] font-semibold text-gray-200"}
                aria-pressed={isOn(item.key)}
              >
                {isOn(item.key) ? "ON" : "OFF"}
              </button>
            </label>
          ))}
        </div>
      </div>
      {isOn("kpiSection") && <KpiSection periodLabel={periodLabel} />}
      {isOn("postScraperKpis") && <PostScraperKpiSection maxRunId={selectedSnapshotRunId} />}

      {(showTrends || showTopProfiles) && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {showTrends && (
            <div className={showTopProfiles ? "lg:col-span-2 grid grid-cols-1 gap-4" : "lg:col-span-3 grid grid-cols-1 gap-4"}>
              {isOn("followerGrowth") && <FollowerGrowthChart upToPeriodLabel={periodLabel} />}
              {isOn("postVolume") && <PostVolumeChart upToPeriodLabel={periodLabel} />}
            </div>
          )}
          {showTopProfiles && <TopProfilesTable />}
        </div>
      )}

      {showAccountBenchmarks && (
        <div className={isOn("accountSummary") && isOn("gradeBenchmarks") ? "grid grid-cols-1 lg:grid-cols-2 gap-4" : "grid grid-cols-1 gap-4"}>
          {isOn("accountSummary") && <AccountSummaryTable periodLabel={periodLabel} />}
          {isOn("gradeBenchmarks") && <GradeBenchmarksChart periodLabel={periodLabel} />}
        </div>
      )}

      {showHashtagHeatmap && (
        <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">
          {isOn("hashtagPerformance") && (
            <div className={isOn("postingTimeHeatmap") ? "xl:col-span-2" : "xl:col-span-5"}>
              <HashtagPerformanceCard periodLabel={periodLabel} />
            </div>
          )}
          {isOn("postingTimeHeatmap") && (
            <div className={isOn("hashtagPerformance") ? "xl:col-span-3" : "xl:col-span-5"}>
              <PostingTimeHeatmap periodLabel={periodLabel} />
            </div>
          )}
        </div>
      )}

      {showRunAndSemantic && (
        <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">
          {isOn("scrapeRunSummary") && (
            <div className={isOn("semanticPostSearch") ? "xl:col-span-2" : "xl:col-span-5"}>
              <ScrapeRunSummaryTable maxRunId={selectedSnapshotRunId} />
            </div>
          )}
          {isOn("semanticPostSearch") && (
            <div className={isOn("scrapeRunSummary") ? "xl:col-span-3" : "xl:col-span-5"}>
              <SemanticPostSearch />
            </div>
          )}
        </div>
      )}
    </div>
  )
}
