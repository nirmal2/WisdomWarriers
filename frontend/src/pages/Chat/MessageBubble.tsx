import type { Message } from "../../hooks/useChat"
import { SourceCards } from "./SourceCards"
import { clsx } from "clsx"

interface Props {
  message: Message
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user"
  return (
    <div className={clsx("flex", isUser ? "justify-end" : "justify-start")}>
      <div className={clsx("max-w-[75%]", isUser ? "items-end" : "items-start", "flex flex-col gap-1")}>
        <div
          className={clsx(
            "rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap break-words",
            isUser
              ? "bg-purple-700 text-white rounded-br-sm"
              : "bg-gray-800 text-gray-100 rounded-bl-sm"
          )}
        >
          {message.content}
        </div>
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="w-full">
            <SourceCards sources={message.sources} />
          </div>
        )}
      </div>
    </div>
  )
}
