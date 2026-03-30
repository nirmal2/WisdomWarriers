export interface OverviewStats {
  total_profiles: number
  total_posts: number
  avg_followers: number
  top_profile: string
}

export interface TimeSeriesPoint {
  period_label: string
  followers_count: number
  username: string
}

export interface TopProfile {
  username: string
  value: number
}

export interface HashtagFrequency {
  tag: string
  count: number
}

export interface EngagementByProfile {
  owner_username: string
  avg_likes: number
  avg_plays: number
  post_count: number
}

export interface PostVolume {
  period_label: string
  post_count: number
}
