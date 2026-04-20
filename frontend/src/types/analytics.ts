export interface OverviewStats {
  total_profiles: number
  total_posts: number
  avg_followers: number
  top_profile: string
  latest_period: string | null
  active_accounts: number
  avg_engagement_rate: number
  top_hashtag: string | null
}

export interface TimeSeriesPoint {
  period_label: string
  followers_count: number
  username: string
  follower_delta?: number | null
  follower_delta_pct?: number | null
  scraped_at?: string
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

export interface AccountSummary {
  owner_username: string
  period_label: string
  grade: string | null
  category: string | null
  posts_count: number
  avg_likes: number
  avg_comments: number
  avg_video_views: number
  total_likes: number
  total_comments: number
  peak_likes: number
  peak_comments: number
  avg_engagement_rate: number
  peak_engagement_rate: number
  image_count: number
  video_count: number
  carousel_count: number
  most_active_day: string | null
}

export interface GradeBenchmark {
  grade: string | null
  category: string | null
  account_count: number
  avg_engagement_rate: number
  avg_likes: number
  avg_comments: number
  avg_followers: number
  period_label: string
}

export interface HashtagPerformance {
  tag: string
  owner_username: string
  period_label: string
  grade: string | null
  category: string | null
  post_count: number
  avg_likes: number
  avg_comments: number
  avg_engagement_rate: number
  total_likes: number
  peak_engagement_rate: number
}

export interface PostingTimeHeatmapPoint {
  day_name: string
  day_of_week: number
  hour_of_day: number
  post_count: number
  avg_likes: number
  avg_comments: number
  avg_engagement_rate: number
}

export interface ScrapeRunSummary {
  id: number
  scraper_type: string
  trigger: string
  started_at: string
  finished_at: string | null
  status: string
  embedding_status: string
  items_fetched: number
  profiles_requested: number
  error_message: string | null
  embedding_error_message: string | null
  schedule_name: string | null
  schedule_frequency: string | null
  duration_seconds: number | null
}

export interface SemanticPostResult {
  id: string
  short_code: string
  owner_username: string
  caption: string | null
  display_url: string | null
  likes_count: number
  engagement_rate: number
  similarity: number
}

export interface PostEngagementHistoryPoint {
  post_id: string
  short_code: string
  owner_username: string
  period_label: string
  scraped_at: string
  likes_count: number
  type: string | null
  display_storage_url: string | null
  caption: string | null
  hashtags: string[] | null
  run_id: number | null
  followers_count: number | null
  likes_rate: number
}
