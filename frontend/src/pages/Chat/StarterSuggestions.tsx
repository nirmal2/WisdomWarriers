interface Props {
  onSelect: (text: string) => void
}

const SUGGESTIONS = [
  "Which accounts gained the most followers this week?",
  "Show me posts with the most likes in March",
  "What are the top trending hashtags?",
  "Compare engagement rates across tracked profiles",
  "Which profile has the highest follower growth rate?",
  "Show recent posts mentioning fitness",
]

export function StarterSuggestions({ onSelect }: Props) {
  return (
    <div className="px-4 pb-4">
      <p className="text-sm text-gray-500 text-center mb-3">Ask anything about your tracked Instagram data</p>
      <div className="grid grid-cols-2 gap-2">
        {SUGGESTIONS.map(s => (
          <button
            key={s}
            onClick={() => onSelect(s)}
            className="text-left text-xs text-gray-300 bg-gray-900 border border-gray-800 hover:border-purple-600 hover:text-white rounded-lg px-3 py-2 transition-colors"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}
