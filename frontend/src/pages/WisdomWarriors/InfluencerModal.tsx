import { useState } from "react"
import { X } from "lucide-react"
import type { WisdomWarrior, WisdomWarriorCreate, InfluencerCategory, InfluencerGrade } from "../../types/wisdomWarrior"

const CATEGORIES: InfluencerCategory[] = ["Dedicated", "In-house influencer"]
const GRADES: InfluencerGrade[] = ["A", "B", "C", "D", "E", "Inactive"]

interface Props {
  onSubmit: (data: WisdomWarriorCreate) => void
  onClose: () => void
  initialData?: WisdomWarrior
}

export function InfluencerModal({ onSubmit, onClose, initialData }: Props) {
  const [username, setUsername] = useState(initialData?.username ?? "")
  const [category, setCategory] = useState<InfluencerCategory | "">(initialData?.category ?? "")
  const [grade, setGrade] = useState<InfluencerGrade | "">(initialData?.grade ?? "")
  const [error, setError] = useState("")

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!username.trim()) {
      setError("Username is required.")
      return
    }
    onSubmit({
      username: username.trim(),
      category: category || null,
      grade: grade || null,
    })
  }

  const fieldClass =
    "w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-500 outline-none focus:border-purple-500"
  const labelClass = "block text-xs font-medium text-gray-400 mb-1"

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-sm mx-4 shadow-2xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-800">
          <h2 className="text-sm font-semibold text-gray-100">
            {initialData ? "Edit Influencer" : "Add Influencer"}
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 transition-colors">
            <X size={16} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-5 py-4 space-y-4">
          <div>
            <label className={labelClass}>Username *</label>
            <input
              className={fieldClass}
              placeholder="e.g. johndoe"
              value={username}
              onChange={e => { setUsername(e.target.value); setError("") }}
            />
            {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
          </div>

          <div>
            <label className={labelClass}>Category</label>
            <select
              className={fieldClass}
              value={category}
              onChange={e => setCategory(e.target.value as InfluencerCategory | "")}
            >
              <option value="">— None —</option>
              {CATEGORIES.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <div>
            <label className={labelClass}>Grade</label>
            <select
              className={fieldClass}
              value={grade}
              onChange={e => setGrade(e.target.value as InfluencerGrade | "")}
            >
              <option value="">— None —</option>
              {GRADES.map(g => (
                <option key={g} value={g}>{g}</option>
              ))}
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-1.5 text-sm text-gray-400 hover:text-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-1.5 text-sm bg-purple-700 hover:bg-purple-600 text-white rounded-lg transition-colors"
            >
              {initialData ? "Save Changes" : "Add"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
