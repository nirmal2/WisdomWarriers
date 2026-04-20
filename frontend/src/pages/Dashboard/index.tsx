import { KpiSection } from "./KpiSection"
import { TopProfilesTable } from "./TopProfilesTable"
import { AccountSummaryTable } from "./AccountSummaryTable"
import { GradeBenchmarksChart } from "./GradeBenchmarksChart"
import { HashtagPerformanceCard } from "./HashtagPerformanceCard"
import { PostingTimeHeatmap } from "./PostingTimeHeatmap"
import { ScrapeRunSummaryTable } from "./ScrapeRunSummaryTable"
import { SemanticPostSearch } from "./SemanticPostSearch"
import { FollowerGrowthChart } from "../Analytics/FollowerGrowthChart"
import { PostVolumeChart } from "../Analytics/PostVolumeChart"

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-sm text-gray-400 mt-1">View-backed analytics across account performance, hashtag lift, posting times, run health, and semantic post discovery.</p>
      </div>
      <KpiSection />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 grid grid-cols-1 gap-4">
          <FollowerGrowthChart />
          <PostVolumeChart />
        </div>
        <TopProfilesTable />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <AccountSummaryTable />
        <GradeBenchmarksChart />
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">
        <div className="xl:col-span-2">
          <HashtagPerformanceCard />
        </div>
        <div className="xl:col-span-3">
          <PostingTimeHeatmap />
        </div>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">
        <div className="xl:col-span-2">
          <ScrapeRunSummaryTable />
        </div>
        <div className="xl:col-span-3">
          <SemanticPostSearch />
        </div>
      </div>
    </div>
  )
}
