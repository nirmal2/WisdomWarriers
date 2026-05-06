import { API_URL } from "../config"
import type { RunComparison, ScrapeRun } from "../types/schedule"

export interface ScrapeRequest {
  scraper_type: string
  usernames?: string[]
  batch_mode?: boolean
  results_limit?: number
  only_posts_newer_than?: string
  date_from?: string
  date_to?: string
  data_detail_level?: "basicData" | "detailedData"
  enable_embeddings?: boolean
  apify_token?: string
}

export interface CombinedScrapeRequest {
  usernames?: string[]
  batch_mode?: boolean
  results_limit?: number
  only_posts_newer_than?: string
  date_from?: string
  date_to?: string
  data_detail_level?: "basicData" | "detailedData"
  enable_embeddings?: boolean
  apify_token?: string
}

export interface ScrapeStartResponse {
  status: string
  profiles_count: number
  run_id: number
  action?: string
}

export interface ProfilesSourceResponse {
  usernames: string[]
}

export interface ScrapeDbUpdateStatus {
  posts_rows: number
  profile_snapshots_rows: number
  profiles_touched: number
  missing_usernames: string[]
}

export interface ScrapeStatusResponse {
  run: ScrapeRun | null
  progress_pct: number
  db_updates: ScrapeDbUpdateStatus
  resume_detected?: boolean
  logs: string[]
}

export const triggerScrape = (body: ScrapeRequest): Promise<ScrapeStartResponse> =>
  fetch(`${API_URL}/api/scrape/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then(r => r.json())

export const triggerCombinedScrape = (body: CombinedScrapeRequest): Promise<ScrapeStartResponse> =>
  fetch(`${API_URL}/api/scrape/run/combined`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then(r => r.json())

export const fetchRuns = (params: Record<string, string | number | undefined> = {}): Promise<{ items: ScrapeRun[]; total: number }> => {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined) qs.set(k, String(v))
  }
  return fetch(`${API_URL}/api/scrape/runs?${qs}`).then(r => r.json())
}

export const fetchProfilesSource = (): Promise<ProfilesSourceResponse> =>
  fetch(`${API_URL}/api/scrape/profiles-source`).then(r => r.json())

export const updateProfilesSource = (usernames: string[]): Promise<ProfilesSourceResponse> =>
  fetch(`${API_URL}/api/scrape/profiles-source`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ usernames }),
  }).then(r => r.json())

export const fetchScrapeStatus = (runId?: number): Promise<ScrapeStatusResponse> => {
  const qs = new URLSearchParams()
  if (runId !== undefined) qs.set("run_id", String(runId))
  return fetch(`${API_URL}/api/scrape/status?${qs}`).then(r => r.json())
}

export const skipEmbedding = (runId: number): Promise<ScrapeRun> =>
  fetch(`${API_URL}/api/scrape/runs/${runId}/skip-embedding`, { method: "PATCH" }).then(r => {
    if (!r.ok) return r.json().then(e => Promise.reject(new Error(e.detail ?? "Failed")))
    return r.json()
  })

export const fetchRunComparison = (
  runAId: number,
  runBId: number,
  profileLimit = 50,
  latestPostLimit = 50,
): Promise<RunComparison> => {
  const qs = new URLSearchParams({
    run_a_id: String(runAId),
    run_b_id: String(runBId),
    profile_limit: String(profileLimit),
    latest_post_limit: String(latestPostLimit),
  })
  return fetch(`${API_URL}/api/scrape/runs/compare?${qs}`).then(async r => {
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: "Failed to compare runs" }))
      throw new Error(err.detail ?? "Failed to compare runs")
    }
    return r.json()
  })
}
