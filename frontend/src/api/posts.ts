import { API_URL } from "../config"
import type { PostListResponse, PostQueryParams } from "../types/post"

export async function fetchPosts(params: PostQueryParams = {}): Promise<PostListResponse> {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (Array.isArray(v)) {
      for (const item of v) {
        if (item !== undefined && item !== "") qs.append(k, String(item))
      }
    } else if (v !== undefined && v !== "") {
      qs.set(k, String(v))
    }
  }
  const res = await fetch(`${API_URL}/api/posts?${qs}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}
