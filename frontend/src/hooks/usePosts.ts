import { useQuery } from "@tanstack/react-query"
import { fetchPosts } from "../api/posts"

export function usePosts(params: Record<string, string | number | undefined> = {}) {
  return useQuery({
    queryKey: ["posts", params],
    queryFn: () => fetchPosts(params),
  })
}
