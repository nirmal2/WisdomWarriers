export interface Profile {
  id: string
  username: string
  url?: string
  full_name?: string
  biography?: string
  followers_count: number
  follows_count: number
  posts_count: number
  is_verified: boolean
  is_private: boolean
  is_business_account: boolean
  business_category?: string
  profile_pic_url?: string
  external_url?: string
  igtv_video_count: number
  highlight_reel_count: number
  joined_recently: boolean
  has_channel: boolean
  first_seen_at?: string
  last_updated_at?: string
}

export interface Snapshot {
  id: number
  scraped_at: string
  followers_count: number
  follows_count: number
  posts_count: number
  period_label: string
}

export interface ProfileDetail extends Profile {
  snapshots: Snapshot[]
}

export interface ProfileListResponse {
  items: Profile[]
  total: number
}
