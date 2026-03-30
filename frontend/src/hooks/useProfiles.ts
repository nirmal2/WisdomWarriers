import { useQuery } from "@tanstack/react-query"
import { fetchProfiles, fetchProfile } from "../api/profiles"

export function useProfiles(params: Record<string, string | number | boolean | undefined> = {}) {
  return useQuery({
    queryKey: ["profiles", params],
    queryFn: () => fetchProfiles(params),
  })
}

export function useProfile(username: string) {
  return useQuery({
    queryKey: ["profile", username],
    queryFn: () => fetchProfile(username),
    enabled: !!username,
  })
}
