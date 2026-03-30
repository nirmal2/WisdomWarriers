import { useEffect, useRef } from "react"
import type { Message } from "../../hooks/useChat"
import { MessageBubble } from "./MessageBubble"

interface Props {
  messages: Message[]
  loading: boolean
}

export function MessageThread({ messages, loading }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, loading])
  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
      {messages.map((m, i) => (
        <MessageBubble key={i} message={m} />
      ))}
      {loading && (
        <div className="flex justify-start">
          <div className="bg-gray-800 rounded-2xl rounded-bl-sm px-4 py-2.5">
            <span className="flex gap-1">
              {[0, 150, 300].map(d => (
                <span
                  key={d}
                  className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: `${d}ms` }}
                />
              ))}
            </span>
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  )
}
