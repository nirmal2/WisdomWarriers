import { useQuery } from "@tanstack/react-query"
import { fetchPosts } from "../api/posts"
import type { PostQueryParams } from "../types/post"

export function usePosts(params: PostQueryParams = {}) {
  return useQuery({
    queryKey: ["posts", params],
    queryFn: () => fetchPosts(params),
  })
}
