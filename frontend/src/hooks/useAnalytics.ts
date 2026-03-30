import { useQuery } from "@tanstack/react-query"
import {
  fetchOverview, fetchFollowerGrowth, fetchTopProfiles,
  fetchHashtagFrequency, fetchEngagement, fetchPostVolume,
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
