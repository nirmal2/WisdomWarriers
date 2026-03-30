import { useState } from "react"

interface FiltersProps {
  onFilter: (params: Record<string, string | number | undefined>) => void
}

export function PostFilters({ onFilter }: FiltersProps) {
  const [username, setUsername] = useState("")
  const [hashtag, setHashtag] = useState("")
  const [dateFrom, setDateFrom] = useState("")
  const [likesMin, setLikesMin] = useState("")

  const apply = () => onFilter({
    username: username || undefined,
    hashtag: hashtag || undefined,
    date_from: dateFrom || undefined,
    likes_min: likesMin ? Number(likesMin) : undefined,
  })

  return (
    <div className="flex flex-wrap gap-2 mb-4">
      <input placeholder="Username" value={username} onChange={e => setUsername(e.target.value)}
        className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-200 w-40" />
      <input placeholder="Hashtag" value={hashtag} onChange={e => setHashtag(e.target.value)}
        className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-200 w-36" />
      <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)}
        className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-200" />
      <input placeholder="Min likes" type="number" value={likesMin} onChange={e => setLikesMin(e.target.value)}
        className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-200 w-28" />
      <button onClick={apply} className="px-3 py-1.5 text-sm bg-blue-700 hover:bg-blue-600 rounded-lg transition-colors">
        Apply
      </button>
    </div>
  )
}
