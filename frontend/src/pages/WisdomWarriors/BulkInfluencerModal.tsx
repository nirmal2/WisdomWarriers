import { useMemo, useState } from "react"
import { ClipboardPaste, Plus, Trash2, Upload, X } from "lucide-react"
import type { InfluencerCategory, InfluencerGrade, WisdomWarriorCreate } from "../../types/wisdomWarrior"

const CATEGORIES: InfluencerCategory[] = ["Dedicated", "In-house influencer"]
const GRADES: InfluencerGrade[] = ["A", "B", "C", "D", "E", "Inactive"]

interface Props {
  initialCategory: InfluencerCategory
  isSubmitting?: boolean
  onSubmit: (items: WisdomWarriorCreate[]) => void
  onClose: () => void
}

type BulkEntryRow = {
  id: number
  username: string
  grade: InfluencerGrade | ""
  category: InfluencerCategory
}

let nextRowId = 1

function createEmptyRow(category: InfluencerCategory, grade: InfluencerGrade | "" = ""): BulkEntryRow {
  return {
    id: nextRowId++,
    username: "",
    grade,
    category,
  }
}

function createEmptyRows(
  category: InfluencerCategory,
  count: number,
  grade: InfluencerGrade | "" = ""
): BulkEntryRow[] {
  return Array.from({ length: count }, () => createEmptyRow(category, grade))
}

function normalizeUsername(value: string) {
  let cleaned = value.trim()
  cleaned = cleaned.replace(/^@/, "")
  cleaned = cleaned.replace(/\?.*$/, "")
  cleaned = cleaned.replace(/\/+$/, "")

  const instagramMatch = cleaned.match(/instagram\.com\/([^/?#]+)/i)
  if (instagramMatch?.[1]) return instagramMatch[1].trim()

  return cleaned.includes("/") ? cleaned.split("/").filter(Boolean).pop() ?? "" : cleaned
}

function normalizeGrade(value: string | undefined, fallback: InfluencerGrade | "") {
  const normalized = value?.trim().toLowerCase() ?? ""
  if (!normalized) return fallback
  return GRADES.find(option => option.toLowerCase() === normalized) ?? fallback
}

function normalizeCategory(value: string | undefined, fallback: InfluencerCategory) {
  const normalized = value?.trim().toLowerCase() ?? ""
  if (!normalized) return fallback
  if (normalized.startsWith("ded")) return "Dedicated"
  if (normalized.includes("house")) return "In-house influencer"
  return fallback
}

function parseGridInput(
  input: string,
  fallbackCategory: InfluencerCategory,
  fallbackGrade: InfluencerGrade | ""
): Array<Omit<BulkEntryRow, "id">> {
  const items: Array<Omit<BulkEntryRow, "id">> = []

  for (const rawLine of input.split(/\r?\n/)) {
    const line = rawLine.trim()
    if (!line) continue

    const parts = line.includes("\t")
      ? line.split("\t").map(part => part.trim())
      : line.split(/[|,]/).map(part => part.trim())

    const username = normalizeUsername(parts[0] ?? "")
    if (!username) continue

    items.push({
      username,
      grade: normalizeGrade(parts[1], fallbackGrade),
      category: normalizeCategory(parts[2], fallbackCategory),
    })
  }

  return items
}

function buildItems(rows: BulkEntryRow[]): WisdomWarriorCreate[] {
  const seen = new Set<string>()
  const items: WisdomWarriorCreate[] = []

  for (const row of rows) {
    const username = normalizeUsername(row.username)
    if (!username) continue

    const key = username.toLowerCase()
    if (seen.has(key)) continue
    seen.add(key)

    items.push({
      username,
      category: row.category,
      grade: row.grade || null,
    })
  }

  return items
}

export function BulkInfluencerModal({ initialCategory, isSubmitting = false, onSubmit, onClose }: Props) {
  const [defaultCategory, setDefaultCategory] = useState<InfluencerCategory>(initialCategory)
  const [defaultGrade, setDefaultGrade] = useState<InfluencerGrade | "">("")
  const [rows, setRows] = useState<BulkEntryRow[]>(() => createEmptyRows(initialCategory, 8))
  const [pasteText, setPasteText] = useState("")
  const [error, setError] = useState("")

  const readyItems = useMemo(() => buildItems(rows), [rows])

  function updateRow(id: number, patch: Partial<BulkEntryRow>) {
    setRows(prev => prev.map(row => (row.id === id ? { ...row, ...patch } : row)))
  }

  function addRows(count = 3) {
    setRows(prev => [...prev, ...createEmptyRows(defaultCategory, count, defaultGrade)])
  }

  function removeRow(id: number) {
    setRows(prev => (prev.length <= 1 ? prev : prev.filter(row => row.id !== id)))
  }

  function importRows(text: string, startIndex = 0) {
    const parsedRows = parseGridInput(text, defaultCategory, defaultGrade)
    if (parsedRows.length === 0) {
      setError("Paste at least one valid username row.")
      return
    }

    setRows(prev => {
      const next = [...prev]
      while (next.length < startIndex + parsedRows.length) {
        next.push(createEmptyRow(defaultCategory, defaultGrade))
      }

      parsedRows.forEach((row, offset) => {
        const targetIndex = startIndex + offset
        const target = next[targetIndex] ?? createEmptyRow(defaultCategory, defaultGrade)
        next[targetIndex] = {
          ...target,
          username: row.username,
          grade: row.grade,
          category: row.category,
        }
      })

      if (next.every(row => row.username.trim())) {
        next.push(...createEmptyRows(defaultCategory, 3, defaultGrade))
      }

      return next
    })

    setPasteText("")
    setError("")
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (readyItems.length === 0) {
      setError("Add at least one valid username.")
      return
    }
    onSubmit(readyItems)
  }

  function handleCellPaste(rowIndex: number, e: React.ClipboardEvent<HTMLInputElement>) {
    const text = e.clipboardData.getData("text")
    if (!text.includes("\n") && !text.includes("\t")) return
    e.preventDefault()
    importRows(text, rowIndex)
  }

  const fieldClass =
    "w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 placeholder-gray-500 outline-none focus:border-purple-500"
  const compactFieldClass =
    "w-full rounded-md border border-gray-700 bg-gray-900 px-2 py-1.5 text-sm text-gray-100 placeholder-gray-500 outline-none focus:border-purple-500"
  const labelClass = "mb-1 block text-xs font-medium text-gray-400"

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="mx-4 max-h-[90vh] w-full max-w-6xl overflow-y-auto rounded-xl border border-gray-700 bg-gray-900 shadow-2xl">
        <div className="flex items-center justify-between border-b border-gray-800 px-5 py-4">
          <div>
            <h2 className="text-sm font-semibold text-gray-100">Bulk Add Influencers</h2>
            <p className="mt-0.5 text-xs text-gray-400">
              Add multiple records in an Excel-like grid or paste rows copied from Excel / CSV.
            </p>
          </div>
          <button onClick={onClose} className="text-gray-500 transition-colors hover:text-gray-300">
            <X size={16} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 px-5 py-4">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <div>
              <label className={labelClass}>Default Category</label>
              <select
                className={fieldClass}
                value={defaultCategory}
                onChange={e => setDefaultCategory(e.target.value as InfluencerCategory)}
              >
                {CATEGORIES.map(option => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </div>

            <div>
              <label className={labelClass}>Default Grade</label>
              <select
                className={fieldClass}
                value={defaultGrade}
                onChange={e => setDefaultGrade(e.target.value as InfluencerGrade | "")}
              >
                <option value="">— None —</option>
                {GRADES.map(option => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </div>

            <div className="flex items-end gap-2">
              <button
                type="button"
                onClick={() => addRows(3)}
                className="inline-flex items-center gap-2 rounded-lg border border-gray-700 px-3 py-2 text-sm text-gray-200 transition-colors hover:bg-gray-800"
              >
                <Plus size={14} />
                Add Rows
              </button>
            </div>
          </div>

          <div className="rounded-xl border border-gray-800 bg-gray-950/50 p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-gray-100">Paste from Excel / CSV</p>
                <p className="mt-0.5 text-xs text-gray-400">
                  Use columns in this order: `Username | Grade | Category`. You can also paste directly into the first Username cell.
                </p>
              </div>
              <button
                type="button"
                onClick={() => importRows(pasteText)}
                className="inline-flex items-center gap-2 rounded-lg border border-purple-700 px-3 py-2 text-sm text-purple-200 transition-colors hover:bg-purple-900/30"
              >
                <ClipboardPaste size={14} />
                Import to Grid
              </button>
            </div>
            <textarea
              rows={3}
              className={`${fieldClass} mt-3`}
              placeholder={"username_one\tA\tDedicated\nusername_two\tB\tIn-house influencer"}
              value={pasteText}
              onChange={e => {
                setPasteText(e.target.value)
                setError("")
              }}
            />
          </div>

          <div className="overflow-hidden rounded-xl border border-gray-800">
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-gray-950 text-xs uppercase tracking-wide text-gray-400">
                  <tr>
                    <th className="w-14 px-3 py-2 text-left font-medium">#</th>
                    <th className="px-3 py-2 text-left font-medium">Username</th>
                    <th className="w-40 px-3 py-2 text-left font-medium">Grade</th>
                    <th className="w-52 px-3 py-2 text-left font-medium">Category</th>
                    <th className="w-16 px-3 py-2 text-right font-medium"> </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800 bg-gray-900/70">
                  {rows.map((row, index) => (
                    <tr key={row.id} className="align-top">
                      <td className="px-3 py-2 text-gray-500">{index + 1}</td>
                      <td className="px-3 py-2">
                        <input
                          className={compactFieldClass}
                          placeholder="@username"
                          value={row.username}
                          onChange={e => {
                            updateRow(row.id, { username: e.target.value })
                            setError("")
                          }}
                          onPaste={e => handleCellPaste(index, e)}
                        />
                      </td>
                      <td className="px-3 py-2">
                        <select
                          className={compactFieldClass}
                          value={row.grade}
                          onChange={e => updateRow(row.id, { grade: e.target.value as InfluencerGrade | "" })}
                        >
                          <option value="">— None —</option>
                          {GRADES.map(option => (
                            <option key={option} value={option}>{option}</option>
                          ))}
                        </select>
                      </td>
                      <td className="px-3 py-2">
                        <select
                          className={compactFieldClass}
                          value={row.category}
                          onChange={e => updateRow(row.id, { category: e.target.value as InfluencerCategory })}
                        >
                          {CATEGORIES.map(option => (
                            <option key={option} value={option}>{option}</option>
                          ))}
                        </select>
                      </td>
                      <td className="px-3 py-2 text-right">
                        <button
                          type="button"
                          onClick={() => removeRow(row.id)}
                          className="rounded-md p-2 text-gray-400 transition-colors hover:bg-gray-800 hover:text-red-300"
                          title="Remove row"
                        >
                          <Trash2 size={14} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {error && <p className="text-xs text-red-400">{error}</p>}

          <div className="rounded-lg border border-gray-800 bg-gray-950 px-3 py-2">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-medium text-gray-100">{readyItems.length} influencer(s) ready</p>
              <span className="text-xs text-gray-500">Default category: {defaultCategory}</span>
            </div>
            <p className="mt-1 text-xs text-gray-400">
              {readyItems.length > 0
                ? readyItems.slice(0, 6).map(item => `@${item.username}`).join(", ") + (readyItems.length > 6 ? " ..." : "")
                : "Fill the grid or paste spreadsheet rows to prepare your bulk upload."}
            </p>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-1.5 text-sm text-gray-400 transition-colors hover:text-gray-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center gap-2 rounded-lg bg-purple-700 px-4 py-1.5 text-sm text-white transition-colors hover:bg-purple-600 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Upload size={14} />
              {isSubmitting ? "Adding..." : "Add All"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
