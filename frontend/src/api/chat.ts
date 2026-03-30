import { API_URL } from "../config"
import type { ChatMessage, ChatEvent } from "../types/chat"

export async function* streamChat(
  messages: ChatMessage[],
  sessionId?: string,
): AsyncGenerator<ChatEvent> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, session_id: sessionId }),
  })
  if (!res.ok) throw new Error(await res.text())

  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  let buf = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })
    const lines = buf.split("\n")
    buf = lines.pop() ?? ""
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue
      const payload = line.slice(6).trim()
      if (payload === "[DONE]") return
      try {
        yield JSON.parse(payload) as ChatEvent
      } catch {
        // ignore malformed
      }
    }
  }
}
