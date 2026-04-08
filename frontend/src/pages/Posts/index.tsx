import { useEffect, useMemo, useState } from "react"
import { usePosts } from "../../hooks/usePosts"
import { PostFilters } from "./PostFilters"
import { ColumnConfigurator } from "./ColumnConfig"
import { DataTable } from "../../components/DataTable"
import type { Post, PostQueryParams } from "../../types/post"
import { format } from "date-fns"

function toPreview(value: unknown, max = 80): string {
  if (value === null || value === undefined) return "-"
  if (typeof value === "string") return value.length > max ? `${value.slice(0, max)}...` : value
  try {
    const serialized = JSON.stringify(value)
    return serialized.length > max ? `${serialized.slice(0, max)}...` : serialized
  } catch {
    return String(value)
  }
}

const POSTS_VISIBLE_COLUMNS_STORAGE_KEY = "insta-analytics.posts.visible-columns"

const ALL_COLUMNS = [
  { key: "id", label: "ID", sortable: true, render: (r: Post) => toPreview(r.id, 28) },
  {
    key: "display_storage_url",
    label: "Thumbnail",
    render: (r: Post) => {
      const imageUrl = r.display_storage_url || r.display_url
      if (!imageUrl) return <span className="text-gray-500">-</span>
      return (
        <a href={r.url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}>
          <img
            src={imageUrl}
            alt={r.caption || r.owner_username || "Post image"}
            className="h-12 w-12 min-w-12 rounded-lg object-cover border border-gray-800 bg-gray-950"
            loading="lazy"
          />
        </a>
      )
    },
  },
  { key: "source_post_id", label: "Source Post ID", sortable: true, render: (r: Post) => r.source_post_id || "-" },
  { key: "short_code", label: "Short Code", sortable: true, render: (r: Post) => r.short_code || "-" },
  { key: "owner_username", label: "Account", sortable: true, render: (r: Post) => <span className="text-blue-400">@{r.owner_username}</span> },
  { key: "owner_full_name", label: "Name", sortable: true, render: (r: Post) => r.owner_full_name || "-" },
  { key: "owner_id", label: "Owner ID", sortable: true },
  { key: "owner_profile_pic_url", label: "Owner Pic URL", sortable: true, render: (r: Post) => r.owner_profile_pic_url ? <a href={r.owner_profile_pic_url} target="_blank" rel="noreferrer" className="text-blue-400 underline" onClick={e => e.stopPropagation()}>Open</a> : "-" },
  { key: "location_name", label: "Location", sortable: true, render: (r: Post) => r.location_name || "-" },
  { key: "location_id", label: "Location ID", sortable: true, render: (r: Post) => r.location_id || "-" },
  { key: "type", label: "Type", sortable: true, render: (r: Post) => r.type || "-" },
  { key: "product_type", label: "Product Type", sortable: true, render: (r: Post) => r.product_type || "-" },
  { key: "likes_count", label: "Likes", sortable: true, render: (r: Post) => r.likes_count.toLocaleString() },
  { key: "comments_count", label: "Comments", sortable: true, render: (r: Post) => r.comments_count.toLocaleString() },
  { key: "video_play_count", label: "Plays", sortable: true, render: (r: Post) => r.video_play_count.toLocaleString() },
  { key: "video_view_count", label: "Views", sortable: true, render: (r: Post) => r.video_view_count.toLocaleString() },
  { key: "video_url", label: "Video URL", sortable: true, render: (r: Post) => r.video_url ? <a href={r.video_url} target="_blank" rel="noreferrer" className="text-blue-400 underline" onClick={e => e.stopPropagation()}>Open</a> : "-" },
  { key: "audio_url", label: "Audio URL", sortable: true, render: (r: Post) => r.audio_url ? <a href={r.audio_url} target="_blank" rel="noreferrer" className="text-blue-400 underline" onClick={e => e.stopPropagation()}>Open</a> : "-" },
  { key: "video_duration", label: "Duration (s)", sortable: true, render: (r: Post) => r.video_duration ? r.video_duration.toFixed(2) : "-" },
  { key: "display_url", label: "Display URL", sortable: true, render: (r: Post) => r.display_url ? <a href={r.display_url} target="_blank" rel="noreferrer" className="text-blue-400 underline" onClick={e => e.stopPropagation()}>Open</a> : "-" },
  { key: "display_storage_path", label: "Display Path", sortable: true, render: (r: Post) => r.display_storage_path || "-" },
  { key: "dimensions_width", label: "Width", sortable: true, render: (r: Post) => r.dimensions_width || "-" },
  { key: "dimensions_height", label: "Height", sortable: true, render: (r: Post) => r.dimensions_height || "-" },
  { key: "is_comments_disabled", label: "Comments Disabled", sortable: true, render: (r: Post) => r.is_comments_disabled ? "Yes" : "No" },
  { key: "caption", label: "Caption", sortable: true, render: (r: Post) => r.caption ? r.caption.slice(0, 100) : "-" },
  { key: "first_comment", label: "First Comment", sortable: true, render: (r: Post) => r.first_comment ? r.first_comment.slice(0, 80) : "-" },
  { key: "alt", label: "Alt Text", sortable: true, render: (r: Post) => r.alt ? r.alt.slice(0, 60) : "-" },
  { key: "input_url", label: "Input URL", sortable: true, render: (r: Post) => r.input_url ? <a href={r.input_url} target="_blank" rel="noreferrer" className="text-blue-400 underline" onClick={e => e.stopPropagation()}>Open</a> : "-" },
  { key: "hashtags", label: "Tags", sortable: true, sortAccessor: (r: Post) => (r.hashtags || []).join(","), render: (r: Post) => (r.hashtags || []).slice(0, 3).join(", ") },
  { key: "mentions", label: "Mentions", sortable: true, sortAccessor: (r: Post) => (r.mentions || []).join(","), render: (r: Post) => (r.mentions || []).slice(0, 3).join(", ") },
  { key: "tagged_users", label: "Tagged Users", sortable: true, render: (r: Post) => (r.tagged_users || []).length },
  { key: "latest_comments", label: "Latest Comments", sortable: true, render: (r: Post) => toPreview(r.latest_comments) },
  { key: "images", label: "Images", sortable: true, render: (r: Post) => (r.images || []).length },
  { key: "child_posts", label: "Child Posts", sortable: true, render: (r: Post) => (r.child_posts || []).length },
  { key: "music_info", label: "Music Info", sortable: true, render: (r: Post) => toPreview(r.music_info) },
  { key: "coauthor_producers", label: "Coauthors", sortable: true, render: (r: Post) => (r.coauthor_producers || []).length },
  { key: "is_pinned", label: "Pinned", sortable: true, render: (r: Post) => r.is_pinned ? "Yes" : "No" },
  { key: "timestamp", label: "Date", sortable: true, sortAccessor: (r: Post) => r.timestamp ?? "", render: (r: Post) => r.timestamp ? format(new Date(r.timestamp), "MMM d, yyyy") : "" },
  { key: "scraped_at", label: "Scraped", sortable: true, sortAccessor: (r: Post) => r.scraped_at ?? "", render: (r: Post) => r.scraped_at ? format(new Date(r.scraped_at), "MMM d HH:mm") : "" },
  { key: "period_label", label: "Period", sortable: true, render: (r: Post) => r.period_label || "-" },
  { key: "profile_id", label: "Profile ID", sortable: true, render: (r: Post) => r.profile_id || "-" },
  { key: "run_id", label: "Run ID", sortable: true, render: (r: Post) => r.run_id || "-" },
  { key: "embedding", label: "Embedding", sortable: true, render: (r: Post) => Array.isArray(r.embedding) ? `${r.embedding.length} dims` : "-" },
  { key: "url", label: "Link", sortable: true, render: (r: Post) => <a href={r.url} target="_blank" rel="noreferrer" className="text-blue-400 underline" onClick={e => e.stopPropagation()}>View</a> },
]

const DEFAULT_VISIBLE_COLUMN_KEYS = [
  "display_storage_url",
  "owner_username",
  "type",
  "likes_count",
  "comments_count",
  "video_play_count",
  "video_view_count",
  "caption",
  "first_comment",
  "mentions",
  "tagged_users",
  "latest_comments",
]

const ALL_COLUMN_KEYS = new Set(ALL_COLUMNS.map(column => column.key))

function getInitialVisibleColumns() {
  const defaultSelection = new Set(DEFAULT_VISIBLE_COLUMN_KEYS)

  if (typeof window === "undefined") {
    return defaultSelection
  }

  try {
    const raw = window.localStorage.getItem(POSTS_VISIBLE_COLUMNS_STORAGE_KEY)
    if (!raw) {
      return defaultSelection
    }

    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) {
      return defaultSelection
    }

    const validKeys = parsed.filter(
      (key): key is string => typeof key === "string" && ALL_COLUMN_KEYS.has(key)
    )

    if (parsed.length > 0 && validKeys.length === 0) {
      return defaultSelection
    }

    return new Set(validKeys)
  } catch {
    return defaultSelection
  }
}

export default function PostsPage() {
  const [filters, setFilters] = useState<PostQueryParams>({})
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const [visibleColumns, setVisibleColumns] = useState<Set<string>>(getInitialVisibleColumns)

  const offset = (page - 1) * pageSize
  const { data, isLoading } = usePosts({ ...filters, limit: pageSize, offset })

  const displayColumns = useMemo(
    () => ALL_COLUMNS.filter(col => visibleColumns.has(col.key)),
    [visibleColumns]
  )

  const total = data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const startRow = total === 0 ? 0 : offset + 1
  const endRow = Math.min(offset + (data?.items.length ?? 0), total)

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages)
    }
  }, [page, totalPages])

  useEffect(() => {
    window.localStorage.setItem(
      POSTS_VISIBLE_COLUMNS_STORAGE_KEY,
      JSON.stringify(Array.from(visibleColumns))
    )
  }, [visibleColumns])

  function handleFilterChange(params: PostQueryParams) {
    setFilters(params)
    setPage(1)
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Posts</h1>
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
        <div className="space-y-4">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div className="flex-1">
              <PostFilters onFilter={handleFilterChange} />
            </div>
            <ColumnConfigurator
              availableColumns={ALL_COLUMNS.map(c => ({ key: c.key, label: c.label }))}
              selectedColumns={visibleColumns}
              onColumnsChange={setVisibleColumns}
            />
          </div>
          {isLoading ? (
            <p className="py-8 text-center text-gray-400">Loading…</p>
          ) : (
            <>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-xs text-gray-500">
                  Showing {startRow}-{endRow} of {total} posts
                </p>
                <div className="flex flex-wrap items-center gap-2">
                  <label className="text-xs text-gray-400">Rows per page</label>
                  <select
                    value={pageSize}
                    onChange={e => {
                      setPageSize(Number(e.target.value))
                      setPage(1)
                    }}
                    className="rounded-lg border border-gray-700 bg-gray-800 px-2 py-1.5 text-sm text-gray-200"
                  >
                    {[25, 50, 100, 200].map(size => (
                      <option key={size} value={size}>{size}</option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={() => setPage(prev => Math.max(1, prev - 1))}
                    disabled={page <= 1}
                    className="rounded-lg border border-gray-700 px-3 py-1.5 text-sm text-gray-200 transition-colors hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <span className="text-sm text-gray-300">
                    Page {page} of {totalPages}
                  </span>
                  <button
                    type="button"
                    onClick={() => setPage(prev => Math.min(totalPages, prev + 1))}
                    disabled={page >= totalPages}
                    className="rounded-lg border border-gray-700 px-3 py-1.5 text-sm text-gray-200 transition-colors hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              </div>
              <DataTable<Post>
                columns={displayColumns as any}
                rows={data?.items ?? []}
                onRowClick={row => {
                  window.open(row.url, "_blank", "noopener,noreferrer")
                }}
              />
            </>
          )}
        </div>
      </div>
    </div>
  )
}
