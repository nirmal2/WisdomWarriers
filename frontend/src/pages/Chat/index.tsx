import { useState, useRef, type KeyboardEvent } from "react"
import { Send, Trash2 } from "lucide-react"
import { useChat } from "../../hooks/useChat"
import { MessageThread } from "./MessageThread"
import { StarterSuggestions } from "./StarterSuggestions"

export default function ChatPage() {
  const { messages, loading, sendMessage, clearChat } = useChat()
  const [input, setInput] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  function send(text?: string) {
    const msg = (text ?? input).trim()
    if (!msg || loading) return
    setInput("")
    sendMessage(msg)
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
        <h1 className="text-lg font-semibold text-white">AI Chat</h1>
        {messages.length > 0 && (
          <button onClick={clearChat} className="flex items-center gap-1 text-xs text-gray-400 hover:text-white transition-colors">
            <Trash2 size={14} /> Clear
          </button>
        )}
      </div>

      {messages.length === 0 ? (
        <div className="flex flex-col flex-1 justify-end">
          <StarterSuggestions onSelect={text => send(text)} />
        </div>
      ) : (
        <MessageThread messages={messages} loading={loading} />
      )}

      <div className="px-4 py-3 border-t border-gray-800">
        <div className="flex items-end gap-2 bg-gray-900 border border-gray-700 rounded-xl px-3 py-2">
          <textarea
            ref={textareaRef}
            rows={1}
            className="flex-1 bg-transparent text-sm text-white resize-none outline-none placeholder-gray-500 max-h-40"
            placeholder="Ask about your Instagram data…"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={onKeyDown}
          />
          <button
            disabled={!input.trim() || loading}
            onClick={() => send()}
            className="flex-shrink-0 p-1.5 rounded-lg bg-purple-700 hover:bg-purple-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <Send size={14} className="text-white" />
          </button>
        </div>
        <p className="text-[10px] text-gray-600 text-center mt-1">Shift+Enter for new line · Enter to send</p>
      </div>
    </div>
  )
}
