import { HashtagChart } from "./HashtagChart"
import { FollowerGrowthChart } from "./FollowerGrowthChart"
import { PostVolumeChart } from "./PostVolumeChart"
import { EngagementChart } from "./EngagementChart"

export default function AnalyticsPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Analytics</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <FollowerGrowthChart />
        <PostVolumeChart />
        <HashtagChart />
        <EngagementChart />
      </div>
    </div>
  )
}
