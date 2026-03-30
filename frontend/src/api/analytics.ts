import { API_URL } from "../config"
import type { OverviewStats, TimeSeriesPoint, TopProfile, HashtagFrequency, EngagementByProfile, PostVolume } from "../types/analytics"

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
