import type { SourceItem } from "../../types/chat"

interface Props {
  sources: SourceItem[]
}

export function SourceCards({ sources }: Props) {
  if (!sources.length) return null
  return (
    <div className="flex gap-2 overflow-x-auto pt-2 pb-1 scrollbar-thin">
      {sources.map((src, i) => (
        <div key={i} className="flex-shrink-0 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 min-w-[140px] max-w-[180px]">
          {src.type === "profile" ? (
            <>
              <div className="flex items-center gap-1.5 mb-1">
                <span className="w-5 h-5 rounded-full bg-purple-700 text-xs flex items-center justify-center text-white font-bold">
                  {src.username?.[0]?.toUpperCase()}
                </span>
                <span className="text-xs font-medium text-white truncate">@{src.username}</span>
              </div>
              <p className="text-[10px] text-gray-400">Profile · score {src.score.toFixed(2)}</p>
            </>
          ) : (
            <>
              <div className="flex items-center gap-1.5 mb-1">
                <span className="text-purple-400 text-xs">🔗</span>
                <span className="text-xs font-medium text-white truncate">@{src.username}</span>
              </div>
              <p className="text-[10px] text-gray-400">Post · score {src.score.toFixed(2)}</p>
            </>
          )}
        </div>
      ))}
    </div>
  )
}
