export interface Schedule {
  id: number
  name: string
  scraper_type: string
  frequency: string
  cron_expr?: string
  is_active: boolean
  batch_mode: boolean
  results_limit: number
  only_posts_newer_than?: string
  actor_id?: string
  last_run_at?: string
  next_run_at?: string
  created_at: string
}

export interface ScheduleCreate {
  name: string
  scraper_type: string
  frequency: string
  cron_expr?: string
  is_active?: boolean
  batch_mode?: boolean
  results_limit?: number
  only_posts_newer_than?: string
}

export interface ScrapeRun {
  id: number
  scraper_type: string
  trigger: string
  schedule_id?: number
  started_at: string
  finished_at?: string
  status: string
  embedding_status: string
  profiles_requested: number
  items_fetched: number
  error_message?: string
  embedding_error_message?: string
  resume_detected?: boolean
}

export interface ScrapeDbUpdateStatus {
  posts_rows: number
  profile_snapshots_rows: number
  profiles_touched: number
  missing_usernames?: string[]
}

export interface ScrapeProfileFailure {
  username: string
  attempt_count: number
  error_message?: string
}

export interface ScrapeProfileAttempt {
  username: string
  status: string
  attempt_count: number
}

export interface ScrapeProfileProgress {
  total_profiles: number
  completed_count: number
  pending_count: number
  failed_count: number
  running_count: number
  completed_profiles: string[]
  pending_profiles: string[]
  failed_profiles: ScrapeProfileFailure[]
  zero_posts_profiles: string[]
  profile_attempts: ScrapeProfileAttempt[]
  server_failure_message?: string
}

export interface ScrapeStatus {
  run: ScrapeRun | null
  progress_pct: number
  db_updates: ScrapeDbUpdateStatus
  profile_progress?: ScrapeProfileProgress
  resume_detected?: boolean
  logs: string[]
}

export interface CompareSummary {
  run_a_profile_snapshot_rows: number
  run_b_profile_snapshot_rows: number
  run_a_latest_posts_rows: number
  run_b_latest_posts_rows: number
  common_profiles: number
  new_profiles: number
  missing_profiles: number
  net_followers_delta: number
  common_latest_posts: number
  new_latest_posts: number
  missing_latest_posts: number
  net_likes_delta: number
}

export interface ProfileDelta {
  profile_id: string
  followers_run_a: number | null
  followers_run_b: number | null
  follows_run_a: number | null
  follows_run_b: number | null
  posts_run_a: number | null
  posts_run_b: number | null
  followers_delta: number
  follows_delta: number
  posts_delta: number
  change_type: "common" | "new" | "missing"
}

export interface LatestPostDelta {
  profile_id: string
  owner_username: string | null
  url: string
  likes_run_a: number | null
  likes_run_b: number | null
  comments_run_a: number | null
  comments_run_b: number | null
  views_run_a: number | null
  views_run_b: number | null
  likes_delta: number
  comments_delta: number
  views_delta: number
  change_type: "common" | "new" | "missing"
}

export interface CompareInsight {
  title: string
  value: string
  detail: string
  tone: "positive" | "negative" | "neutral"
}

export interface RunComparison {
  run_a: ScrapeRun
  run_b: ScrapeRun
  summary: CompareSummary
  profile_deltas: ProfileDelta[]
  latest_post_deltas: LatestPostDelta[]
  insights: CompareInsight[]
}
