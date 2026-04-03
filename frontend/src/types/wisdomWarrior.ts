export type InfluencerCategory = "Dedicated" | "In-house influencer"
export type InfluencerGrade = "A" | "B" | "C" | "D" | "E" | "Inactive"

export interface WisdomWarrior {
  id: number
  username: string
  category: InfluencerCategory | null
  grade: InfluencerGrade | null
  position: number
  profile_pic_url?: string | null
}

export interface WisdomWarriorCreate {
  username: string
  category?: InfluencerCategory | null
  grade?: InfluencerGrade | null
}

export interface WisdomWarriorBulkResult {
  created: WisdomWarrior[]
  skipped_existing: string[]
}

export interface WisdomWarriorUpdate {
  username?: string
  category?: InfluencerCategory | null
  grade?: InfluencerGrade | null
}
