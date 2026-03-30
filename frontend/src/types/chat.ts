export interface ChatMessage {
  role: "user" | "assistant"
  content: string
}

export interface SourceItem {
  type: "profile" | "post"
  username?: string
  url?: string
  score: number
}

export interface ChatEvent {
  type: "sources" | "text"
  content?: string
  data?: SourceItem[]
  session_id?: string
}
