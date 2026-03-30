import { API_URL } from "../config"
import type { PostListResponse } from "../types/post"

export async function fetchPosts(params: Record<string, string | number | undefined> = {}): Promise<PostListResponse> {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined) qs.set(k, String(v))
  }
  const res = await fetch(`${API_URL}/api/posts?${qs}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}
