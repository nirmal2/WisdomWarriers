import { useState } from "react"

interface FiltersProps {
  onFilter: (params: Record<string, string | number | boolean | undefined>) => void
}

export function ProfileFilters({ onFilter }: FiltersProps) {
  const [search, setSearch] = useState("")
  const [verified, setVerified] = useState<string>("")
  const [business, setBusiness] = useState<string>("")
  const [followersMin, setFollowersMin] = useState("")

  const apply = () => {
    onFilter({
      search: search || undefined,
      verified: verified === "" ? undefined : verified === "true",
      business: business === "" ? undefined : business === "true",
      followers_min: followersMin ? Number(followersMin) : undefined,
    })
  }

  return (
    <div className="flex flex-wrap gap-2 mb-4">
      <input
        placeholder="Search username..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-200 w-48"
      />
      <select value={verified} onChange={e => setVerified(e.target.value)}
        className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-200">
        <option value="">Verified: All</option>
        <option value="true">Verified</option>
        <option value="false">Not Verified</option>
      </select>
      <select value={business} onChange={e => setBusiness(e.target.value)}
        className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-200">
        <option value="">Business: All</option>
        <option value="true">Business</option>
        <option value="false">Personal</option>
      </select>
      <input
        placeholder="Min followers"
        type="number"
        value={followersMin}
        onChange={e => setFollowersMin(e.target.value)}
        className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-200 w-36"
      />
      <button onClick={apply} className="px-3 py-1.5 text-sm bg-blue-700 hover:bg-blue-600 rounded-lg transition-colors">
        Apply
      </button>
    </div>
  )
}
