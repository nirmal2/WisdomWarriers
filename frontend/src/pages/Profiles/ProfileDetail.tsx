import { useParams } from "react-router-dom"
import { useProfile } from "../../hooks/useProfiles"
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts"
import { ChartCard } from "../../components/ChartCard"

export function ProfileDetail() {
  const { username } = useParams<{ username: string }>()
  const { data: profile, isLoading } = useProfile(username!)

  if (isLoading) return <p className="text-gray-400 p-8">Loading…</p>
  if (!profile) return <p className="text-red-400 p-8">Profile not found</p>

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-4">
        {profile.profile_pic_url && (
          <img src={profile.profile_pic_url} alt={profile.username} className="w-16 h-16 rounded-full" />
        )}
        <div className="min-w-0 flex-1">
          <h2 className="text-lg md:text-xl font-bold break-all">@{profile.username}</h2>
          <p className="text-gray-400 text-sm">{profile.full_name}</p>
          {profile.biography && <p className="text-gray-300 text-sm mt-1 max-w-lg">{profile.biography}</p>}
        </div>
        <div className="ml-auto grid grid-cols-3 gap-4 text-center">
          <div><p className="text-xl font-bold">{profile.followers_count.toLocaleString()}</p><p className="text-xs text-gray-400">Followers</p></div>
          <div><p className="text-xl font-bold">{profile.follows_count.toLocaleString()}</p><p className="text-xs text-gray-400">Following</p></div>
          <div><p className="text-xl font-bold">{profile.posts_count.toLocaleString()}</p><p className="text-xs text-gray-400">Posts</p></div>
        </div>
      </div>
      {profile.snapshots.length > 1 && (
        <ChartCard title="Follower Growth">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={profile.snapshots}>
              <XAxis dataKey="period_label" tick={{ fill: "#9ca3af", fontSize: 11 }} />
              <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid #374151" }} />
              <Line type="monotone" dataKey="followers_count" stroke="#60a5fa" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      )}
    </div>
  )
}
