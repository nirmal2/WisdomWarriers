import { useState } from "react"
import { Info, Pencil, Trash2, UserPlus } from "lucide-react"
import { clsx } from "clsx"
import {
  useWisdomWarriors,
  useWisdomWarriorsMonthlyViews,
  useCreateWisdomWarrior,
  useUpdateWisdomWarrior,
  useDeleteWisdomWarrior,
} from "../../hooks/useWisdomWarriors"
import { InfluencerModal } from "./InfluencerModal"
import type { WisdomWarrior, InfluencerCategory, WisdomWarriorCreate } from "../../types/wisdomWarrior"

type Tab = "Dedicated" | "In-house influencer"

const GRADE_COLORS: Record<string, string> = {
  A: "bg-emerald-900/60 text-emerald-300 border-emerald-700",
  B: "bg-blue-900/60 text-blue-300 border-blue-700",
  C: "bg-yellow-900/60 text-yellow-300 border-yellow-700",
  D: "bg-orange-900/60 text-orange-300 border-orange-700",
  E: "bg-red-900/60 text-red-300 border-red-700",
  Inactive: "bg-gray-800 text-gray-400 border-gray-600",
}

function GradeBadge({ grade }: { grade: string | null }) {
  if (!grade) return <span className="text-gray-600 text-xs">—</span>
  return (
    <span
      className={clsx(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border",
        GRADE_COLORS[grade] ?? "bg-gray-800 text-gray-400 border-gray-600"
      )}
    >
      {grade}
    </span>
  )
}

export default function WisdomWarriorsPage() {
  const [activeTab, setActiveTab] = useState<Tab>("Dedicated")
  const [selectedMonth, setSelectedMonth] = useState(() => new Date().toISOString().slice(0, 7))
  const [showModal, setShowModal] = useState(false)
  const [editing, setEditing] = useState<WisdomWarrior | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null)

  const { data: all = [], isLoading } = useWisdomWarriors()
  const { data: monthlyViews = [], isLoading: isMonthlyViewsLoading } = useWisdomWarriorsMonthlyViews(selectedMonth)
  const create = useCreateWisdomWarrior()
  const update = useUpdateWisdomWarrior()
  const remove = useDeleteWisdomWarrior()

  const monthlyViewsByUsername = new Map(
    monthlyViews.map(item => [item.username.toLowerCase(), item.total_views])
  )

  const rows = all.filter(w => w.category === activeTab)

  function handleCreate(data: WisdomWarriorCreate) {
    // Force the category to match the active tab when adding from that tab
    const payload = { ...data, category: (data.category ?? activeTab) as InfluencerCategory }
    create.mutate(payload, { onSuccess: () => setShowModal(false) })
  }

  function handleEdit(data: WisdomWarriorCreate) {
    if (!editing) return
    update.mutate(
      { id: editing.id, body: data },
      { onSuccess: () => setEditing(null) }
    )
  }

  function handleDelete(id: number) {
    remove.mutate(id, { onSuccess: () => setDeleteConfirm(null) })
  }

  const tabs: Tab[] = ["Dedicated", "In-house influencer"]

  return (
    <div className="space-y-4 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Wisdom Warriors</h1>
          <p className="text-sm text-gray-400 mt-0.5">Manage influencer profiles tracked by the scraper</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <label htmlFor="month-select" className="text-xs text-gray-400">Month</label>
            <input
              id="month-select"
              type="month"
              value={selectedMonth}
              onChange={e => setSelectedMonth(e.target.value)}
              className="rounded-lg border border-gray-700 bg-gray-900 px-2 py-1.5 text-sm text-gray-200"
            />
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-purple-700 hover:bg-purple-600 text-white rounded-lg transition-colors"
          >
            <UserPlus size={15} />
            Add Influencer
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-800">
        {tabs.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={clsx(
              "px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px",
              activeTab === tab
                ? "border-purple-500 text-purple-300"
                : "border-transparent text-gray-400 hover:text-gray-200"
            )}
          >
            {tab}
            <span className={clsx(
              "ml-2 text-xs px-1.5 py-0.5 rounded-full",
              activeTab === tab ? "bg-purple-800 text-purple-200" : "bg-gray-800 text-gray-500"
            )}>
              {all.filter(w => w.category === tab).length}
            </span>
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="rounded-xl border border-gray-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-900 text-gray-400 text-xs uppercase tracking-wide">
              <th className="px-4 py-3 text-left font-medium">#</th>
              <th className="px-4 py-3 text-left font-medium">Username</th>
              <th className="px-4 py-3 text-left font-medium">Grade</th>
              <th className="px-4 py-3 text-left font-medium">
                <div className="flex items-center gap-1">
                  <span>Monthly Views ({selectedMonth})</span>
                  <div className="relative group">
                    <Info className="w-3.5 h-3.5 text-gray-500 cursor-help" />
                    <div className="absolute left-1/2 -translate-x-1/2 top-5 z-10 hidden group-hover:block w-56 rounded-lg bg-gray-800 border border-gray-700 px-3 py-2 text-xs text-gray-300 shadow-lg normal-case tracking-normal font-normal">
                      Views are collaborator-adjusted: each post's views are divided by the total number of creators (owner&nbsp;+&nbsp;collaborators).
                    </div>
                  </div>
                </div>
              </th>
              <th className="px-4 py-3 text-right font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {isLoading && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-500 text-sm">
                  Loading…
                </td>
              </tr>
            )}
            {!isLoading && rows.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-500 text-sm">
                  No {activeTab} influencers yet. Click <span className="text-purple-400">Add Influencer</span> to get started.
                </td>
              </tr>
            )}
            {rows.map((warrior, idx) => (
              <tr key={warrior.id} className="bg-gray-950 hover:bg-gray-900 transition-colors">
                <td className="px-4 py-3 text-gray-500">{idx + 1}</td>
                <td className="px-4 py-3 font-medium text-gray-100">
                  <a
                    href={`https://www.instagram.com/${warrior.username}/`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2.5 hover:text-purple-400 transition-colors group"
                  >
                    {warrior.profile_pic_url ? (
                      <img
                        src={warrior.profile_pic_url}
                        alt={warrior.username}
                        className="w-8 h-8 rounded-full object-cover flex-shrink-0 ring-1 ring-gray-700"
                        onError={(e) => {
                          const target = e.currentTarget
                          target.style.display = "none"
                          const next = target.nextElementSibling as HTMLElement | null
                          if (next) next.style.display = "flex"
                        }}
                      />
                    ) : null}
                    <span
                      className="w-8 h-8 rounded-full bg-gray-800 ring-1 ring-gray-700 flex-shrink-0 items-center justify-center text-xs font-semibold text-gray-400 uppercase"
                      style={{ display: warrior.profile_pic_url ? "none" : "flex" }}
                    >
                      {warrior.username.charAt(0)}
                    </span>
                    <span>@{warrior.username}</span>
                  </a>
                </td>
                <td className="px-4 py-3">
                  <GradeBadge grade={warrior.grade} />
                </td>
                <td className="px-4 py-3 text-gray-200">
                  {isMonthlyViewsLoading
                    ? "..."
                    : Math.round(monthlyViewsByUsername.get(warrior.username.toLowerCase()) ?? 0).toLocaleString()}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => setEditing(warrior)}
                      className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
                      title="Edit"
                    >
                      <Pencil size={14} />
                    </button>
                    {deleteConfirm === warrior.id ? (
                      <span className="flex items-center gap-1">
                        <button
                          onClick={() => handleDelete(warrior.id)}
                          className="px-2 py-1 text-xs bg-red-700 hover:bg-red-600 text-white rounded transition-colors"
                        >
                          Confirm
                        </button>
                        <button
                          onClick={() => setDeleteConfirm(null)}
                          className="px-2 py-1 text-xs text-gray-400 hover:text-gray-200 transition-colors"
                        >
                          Cancel
                        </button>
                      </span>
                    ) : (
                      <button
                        onClick={() => setDeleteConfirm(warrior.id)}
                        className="p-1.5 rounded-lg text-gray-400 hover:text-red-400 hover:bg-gray-800 transition-colors"
                        title="Delete"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Unassigned notice */}
      {all.some(w => !w.category) && (
        <p className="text-xs text-gray-500">
          {all.filter(w => !w.category).length} influencer(s) have no category assigned and are not shown in any tab.
        </p>
      )}

      {/* Modals */}
      {showModal && (
        <InfluencerModal
          onSubmit={handleCreate}
          onClose={() => setShowModal(false)}
          initialData={{ id: 0, username: "", category: activeTab, grade: null, position: 0 }}
        />
      )}
      {editing && (
        <InfluencerModal
          onSubmit={handleEdit}
          onClose={() => setEditing(null)}
          initialData={editing}
        />
      )}
    </div>
  )
}
