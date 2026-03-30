import { useState, useCallback, useRef } from "react"
import { streamChat } from "../api/chat"
import type { ChatMessage, SourceItem } from "../types/chat"

export interface Message {
  role: "user" | "assistant"
  content: string
  sources?: SourceItem[]
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const sessionIdRef = useRef<string | undefined>(undefined)

  const sendMessage = useCallback(async (text: string) => {
    const userMsg: Message = { role: "user", content: text }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    const history: ChatMessage[] = [...messages, userMsg].map(m => ({ role: m.role, content: m.content }))
    const aiMsg: Message = { role: "assistant", content: "", sources: [] }
    setMessages(prev => [...prev, aiMsg])
    const aiIndex = messages.length + 1

    try {
      for await (const event of streamChat(history, sessionIdRef.current)) {
        if (event.type === "sources") {
          sessionIdRef.current = event.session_id
          setMessages(prev => prev.map((m, i) => i === aiIndex ? { ...m, sources: event.data } : m))
        } else if (event.type === "text" && event.content) {
          setMessages(prev => prev.map((m, i) =>
            i === aiIndex ? { ...m, content: m.content + event.content } : m
          ))
        }
      }
    } finally {
      setLoading(false)
    }
  }, [messages])

  const clearChat = () => {
    setMessages([])
    sessionIdRef.current = undefined
  }

  return { messages, loading, sendMessage, clearChat }
}
