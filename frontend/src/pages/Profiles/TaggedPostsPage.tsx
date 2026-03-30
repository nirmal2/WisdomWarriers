import { Link, useParams } from "react-router-dom"
import { usePosts } from "../../hooks/usePosts"

export function TaggedPostsPage() {
  const { username } = useParams<{ username: string }>()
  const { data, isLoading } = usePosts({ username, tagged_group: "isha", limit: 100 })

  const posts = data?.items ?? []

  return (
    <div className="space-y-5 p-0">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Tagged Posts</h1>
          <p className="mt-1 text-sm text-gray-400">
            Posts for @{username} matching the Isha-related tagged terms set.
          </p>
        </div>
        <Link to="/profiles" className="rounded-lg border border-gray-800 px-3 py-2 text-sm text-gray-300 transition-colors hover:bg-gray-800 hover:text-white">
          Back to Profiles
        </Link>
      </div>

      {isLoading ? (
        <p className="py-10 text-center text-sm text-gray-400">Loading tagged posts…</p>
      ) : posts.length === 0 ? (
        <div className="rounded-2xl border border-gray-800 bg-gray-900/60 p-8 text-center text-sm text-gray-400">
          No tagged posts matched the configured terms for this profile.
        </div>
      ) : (
        <>
          <p className="text-xs text-gray-500">{data?.total ?? 0} matching posts</p>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
            {posts.map(post => {
              const imageUrl = post.display_storage_url || post.display_url
              return (
                <a
                  key={post.id}
                  href={post.url}
                  target="_blank"
                  rel="noreferrer"
                  className="group overflow-hidden rounded-2xl border border-gray-800 bg-gray-900/60 transition-colors hover:border-indigo-500/60"
                >
                  <div className="aspect-square overflow-hidden bg-gray-950">
                    {imageUrl ? (
                      <img
                        src={imageUrl}
                        alt={post.caption || post.owner_username || "Tagged post"}
                        className="h-full w-full object-cover transition-transform duration-200 group-hover:scale-[1.03]"
                        loading="lazy"
                      />
                    ) : (
                      <div className="flex h-full items-center justify-center text-sm text-gray-500">No image</div>
                    )}
                  </div>
                  <div className="space-y-2 p-3">
                    <p className="text-sm font-semibold text-white">@{post.owner_username || username}</p>
                    <p className="line-clamp-3 text-xs leading-6 text-gray-400">{post.caption || "No caption"}</p>
                  </div>
                </a>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}