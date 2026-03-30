import { KpiSection } from "./KpiSection"
import { TopProfilesTable } from "./TopProfilesTable"
import { FollowerGrowthChart } from "../Analytics/FollowerGrowthChart"
import { PostVolumeChart } from "../Analytics/PostVolumeChart"
import { HashtagChart } from "../Analytics/HashtagChart"
import { EngagementChart } from "../Analytics/EngagementChart"

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-sm text-gray-400 mt-1">Overview of profile growth, posting trends, hashtags, and engagement.</p>
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
        <HashtagChart />
        <EngagementChart />
      </div>
    </div>
  )
}
