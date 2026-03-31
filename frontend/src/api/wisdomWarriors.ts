import { API_URL } from "../config"
import type { WisdomWarrior, WisdomWarriorCreate, WisdomWarriorUpdate } from "../types/wisdomWarrior"

const BASE = `${API_URL}/api/scrape/wisdom-warriors`
const ANALYTICS_BASE = `${API_URL}/api/analytics/wisdom-warriors/monthly-views`

export interface WisdomWarriorMonthlyView {
  username: string
  month: string
  total_views: number
  matched_hashtags: string[]
  matched_mentions: string[]
}

export interface WisdomWarriorMonthlyViewsQuery {
  month: string
  applyFilters: boolean
  category?: string
  hashtags?: string[]
  mentions?: string[]
  keywords?: string[]
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(text || res.statusText)
  }
  if (res.status === 204) return undefined as unknown as T
  return res.json()
}

export const fetchWisdomWarriors = (): Promise<WisdomWarrior[]> =>
  fetch(BASE).then(r => handleResponse<WisdomWarrior[]>(r))

export const createWisdomWarrior = (body: WisdomWarriorCreate): Promise<WisdomWarrior> =>
  fetch(BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then(r => handleResponse<WisdomWarrior>(r))

export const updateWisdomWarrior = (id: number, body: WisdomWarriorUpdate): Promise<WisdomWarrior> =>
  fetch(`${BASE}/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then(r => handleResponse<WisdomWarrior>(r))

export const deleteWisdomWarrior = (id: number): Promise<void> =>
  fetch(`${BASE}/${id}`, { method: "DELETE" }).then(r => handleResponse<void>(r))

export const fetchWisdomWarriorsMonthlyViews = (query: WisdomWarriorMonthlyViewsQuery): Promise<WisdomWarriorMonthlyView[]> => {
  const qs = new URLSearchParams()
  qs.set("month", query.month)
  qs.set("apply_filters", String(query.applyFilters))
  if (query.category) qs.set("category", query.category)
  for (const value of query.hashtags ?? []) qs.append("hashtags", value)
  for (const value of query.mentions ?? []) qs.append("mentions", value)
  for (const value of query.keywords ?? []) qs.append("keywords", value)
  return fetch(`${ANALYTICS_BASE}?${qs.toString()}`).then(r => handleResponse<WisdomWarriorMonthlyView[]>(r))
}
