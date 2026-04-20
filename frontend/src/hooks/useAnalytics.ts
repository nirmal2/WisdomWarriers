import { useQuery } from "@tanstack/react-query"
import {
  fetchOverview, fetchFollowerGrowth, fetchTopProfiles,
  fetchHashtagFrequency, fetchEngagement, fetchPostVolume,
  fetchAccountSummary, fetchGradeBenchmarks, fetchHashtagPerformance,
  fetchPostingTimeHeatmap, fetchScrapeRunSummary, fetchSemanticPostSearch,
  fetchPostEngagementHistory,
} from "../api/analytics"

export const useOverview = () => useQuery({ queryKey: ["analytics", "overview"], queryFn: fetchOverview })

export const useFollowerGrowth = (username?: string) =>
  useQuery({ queryKey: ["analytics", "follower-growth", username], queryFn: () => fetchFollowerGrowth(username) })

export const useTopProfiles = (metric = "followers_count", limit = 10) =>
  useQuery({ queryKey: ["analytics", "top-profiles", metric, limit], queryFn: () => fetchTopProfiles(metric, limit) })

export const useHashtagFrequency = (limit = 20) =>
  useQuery({ queryKey: ["analytics", "hashtags", limit], queryFn: () => fetchHashtagFrequency(limit) })

export const useEngagement = () =>
  useQuery({ queryKey: ["analytics", "engagement"], queryFn: fetchEngagement })

export const usePostVolume = () =>
  useQuery({ queryKey: ["analytics", "post-volume"], queryFn: fetchPostVolume })

export const useAccountSummary = (periodLabel?: string, limit = 12) =>
  useQuery({ queryKey: ["analytics", "account-summary", periodLabel, limit], queryFn: () => fetchAccountSummary(periodLabel, limit) })

export const useGradeBenchmarks = (periodLabel?: string) =>
  useQuery({ queryKey: ["analytics", "grade-benchmarks", periodLabel], queryFn: () => fetchGradeBenchmarks(periodLabel) })

export const useHashtagPerformance = (periodLabel?: string, username?: string, limit = 12) =>
  useQuery({ queryKey: ["analytics", "hashtag-performance", periodLabel, username, limit], queryFn: () => fetchHashtagPerformance(periodLabel, username, limit) })

export const usePostingTimeHeatmap = (username?: string) =>
  useQuery({ queryKey: ["analytics", "posting-time-heatmap", username], queryFn: () => fetchPostingTimeHeatmap(username) })

export const useScrapeRunSummary = (limit = 8) =>
  useQuery({ queryKey: ["analytics", "scrape-run-summary", limit], queryFn: () => fetchScrapeRunSummary(limit) })

export const useSemanticPostSearch = (query: string, username?: string, limit = 8) =>
  useQuery({
    queryKey: ["analytics", "semantic-post-search", query, username, limit],
    queryFn: () => fetchSemanticPostSearch(query, username, limit),
    enabled: query.trim().length > 1,
  })

export const usePostEngagementHistory = (shortCode?: string) =>
  useQuery({
    queryKey: ["analytics", "post-engagement-history", shortCode],
    queryFn: () => fetchPostEngagementHistory(shortCode ?? ""),
    enabled: Boolean(shortCode),
  })
