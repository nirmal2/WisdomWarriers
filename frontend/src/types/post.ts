export interface Post {
  id: string
  source_post_id?: string
  short_code?: string
  owner_username?: string
  owner_full_name?: string
  owner_id?: string
  owner_profile_pic_url?: string
  location_name?: string
  location_id?: string
  url: string
  timestamp?: string
  likes_count: number
  video_play_count: number
  video_view_count: number
  type?: string
  video_url?: string
  audio_url?: string
  video_duration?: number
  display_url?: string
  display_storage_path?: string
  display_storage_url?: string
  dimensions_height?: number
  dimensions_width?: number
  is_comments_disabled: boolean
  alt?: string
  caption?: string
  product_type?: string
  input_url?: string
  comments_count: number
  first_comment?: string
  latest_comments: unknown[]
  images: unknown[]
  child_posts: unknown[]
  music_info: Record<string, unknown>
  hashtags: string[]
  mentions: string[]
  tagged_users: unknown[]
  coauthor_producers: unknown[]
  is_pinned: boolean
  profile_id?: string
  scraped_at?: string
  period_label: string
  run_id?: number
  embedding?: number[]
}

export interface PostListResponse {
  items: Post[]
  total: number
}
