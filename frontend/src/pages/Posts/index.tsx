import { useState, useMemo } from "react"
import { usePosts } from "../../hooks/usePosts"
import { PostFilters } from "./PostFilters"
import { ColumnConfigurator } from "./ColumnConfig"
import { DataTable } from "../../components/DataTable"
import type { Post } from "../../types/post"
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

export default function PostsPage() {
  const [filters, setFilters] = useState<Record<string, string | number | undefined>>({})
  const [visibleColumns, setVisibleColumns] = useState<Set<string>>(
    new Set([
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
    ])
  )
  const { data, isLoading } = usePosts({ ...filters, limit: 100 })

  const displayColumns = useMemo(
    () => ALL_COLUMNS.filter(col => visibleColumns.has(col.key)),
    [visibleColumns]
  )

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Posts</h1>
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <PostFilters onFilter={setFilters} />
            <ColumnConfigurator
              availableColumns={ALL_COLUMNS.map(c => ({ key: c.key, label: c.label }))}
              selectedColumns={visibleColumns}
              onColumnsChange={setVisibleColumns}
            />
          </div>
          {isLoading ? (
            <p className="text-gray-400 py-8 text-center">Loading…</p>
          ) : (
            <>
              <p className="text-xs text-gray-500">{data?.total ?? 0} posts</p>
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
