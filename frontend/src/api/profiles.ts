import { API_URL } from "../config"
import type { ProfileListResponse, ProfileDetail } from "../types/profile"

export async function fetchProfiles(params: Record<string, string | number | boolean | undefined> = {}): Promise<ProfileListResponse> {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined) qs.set(k, String(v))
  }
  const res = await fetch(`${API_URL}/api/profiles?${qs}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function fetchProfile(username: string): Promise<ProfileDetail> {
  const res = await fetch(`${API_URL}/api/profiles/${username}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function fetchProfileUsernames(): Promise<{ usernames: string[] }> {
  const res = await fetch(`${API_URL}/api/profiles/usernames`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}
