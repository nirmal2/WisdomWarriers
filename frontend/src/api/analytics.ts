import { API_URL } from "../config"
import type {
  OverviewStats,
  TimeSeriesPoint,
  TopProfile,
  HashtagFrequency,
  EngagementByProfile,
  PostVolume,
  AccountSummary,
  GradeBenchmark,
  HashtagPerformance,
  PostingTimeHeatmapPoint,
  ScrapeRunSummary,
  SemanticPostResult,
  PostEngagementHistoryPoint,
} from "../types/analytics"


const buildQueryString = (params: Record<string, string | number | undefined>) => {
  const searchParams = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      searchParams.set(key, String(value))
    }
  }
  const query = searchParams.toString()
  return query ? `?${query}` : ""
}

export const fetchOverview = (): Promise<OverviewStats> =>
  fetch(`${API_URL}/api/analytics/overview`).then(r => r.json())

export const fetchFollowerGrowth = (username?: string): Promise<TimeSeriesPoint[]> =>
  fetch(`${API_URL}/api/analytics/follower-growth${username ? `?username=${username}` : ""}`).then(r => r.json())

export const fetchTopProfiles = (metric = "followers_count", limit = 10): Promise<TopProfile[]> =>
  fetch(`${API_URL}/api/analytics/top-profiles?metric=${metric}&limit=${limit}`).then(r => r.json())

export const fetchHashtagFrequency = (limit = 20): Promise<HashtagFrequency[]> =>
  fetch(`${API_URL}/api/analytics/hashtag-frequency?limit=${limit}`).then(r => r.json())

export const fetchEngagement = (): Promise<EngagementByProfile[]> =>
  fetch(`${API_URL}/api/analytics/engagement-by-profile`).then(r => r.json())

export const fetchPostVolume = (): Promise<PostVolume[]> =>
  fetch(`${API_URL}/api/analytics/post-trends`).then(r => r.json())

export const fetchAccountSummary = (periodLabel?: string, limit = 12): Promise<AccountSummary[]> =>
  fetch(`${API_URL}/api/analytics/account-summary${buildQueryString({ period_label: periodLabel, limit })}`).then(r => r.json())

export const fetchGradeBenchmarks = (periodLabel?: string): Promise<GradeBenchmark[]> =>
  fetch(`${API_URL}/api/analytics/grade-benchmarks${buildQueryString({ period_label: periodLabel })}`).then(r => r.json())

export const fetchHashtagPerformance = (periodLabel?: string, username?: string, limit = 12): Promise<HashtagPerformance[]> =>
  fetch(`${API_URL}/api/analytics/hashtag-performance${buildQueryString({ period_label: periodLabel, username, limit })}`).then(r => r.json())

export const fetchPostingTimeHeatmap = (username?: string): Promise<PostingTimeHeatmapPoint[]> =>
  fetch(`${API_URL}/api/analytics/posting-time-heatmap${buildQueryString({ username })}`).then(r => r.json())

export const fetchScrapeRunSummary = (limit = 8): Promise<ScrapeRunSummary[]> =>
  fetch(`${API_URL}/api/analytics/scrape-run-summary${buildQueryString({ limit })}`).then(r => r.json())

export const fetchSemanticPostSearch = (query: string, username?: string, limit = 8): Promise<SemanticPostResult[]> =>
  fetch(`${API_URL}/api/analytics/semantic-post-search${buildQueryString({ query, username, limit })}`).then(async r => {
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: "Failed to search posts" }))
      throw new Error(err.detail ?? "Failed to search posts")
    }
    return r.json()
  })

export const fetchPostEngagementHistory = (shortCode: string): Promise<PostEngagementHistoryPoint[]> =>
  fetch(`${API_URL}/api/analytics/post-engagement-history${buildQueryString({ short_code: shortCode })}`).then(r => r.json())
