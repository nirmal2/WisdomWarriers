import { useState } from "react"
import { useProfiles } from "../../hooks/useProfiles"
import { ProfileFilters } from "./ProfileFilters"
import { ProfilesTable } from "./ProfilesTable"

export default function ProfilesPage() {
  const [filters, setFilters] = useState<Record<string, string | number | boolean | undefined>>({})
  const { data, isLoading } = useProfiles({ ...filters, limit: 100 })

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Profiles</h1>
        <span className="text-xs text-gray-400">{data?.total ?? 0} profiles</span>
      </div>

      <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-4">
        <ProfileFilters onFilter={setFilters} />
      </div>

      {isLoading ? (
        <p className="py-10 text-center text-sm text-gray-400">Loading…</p>
      ) : (
        <ProfilesTable profiles={data?.items ?? []} />
      )}
    </div>
  )
}
