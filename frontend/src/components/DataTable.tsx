import { useMemo, useState } from "react"

interface Column<T> {
  key: keyof T | string
  label: string
  render?: (row: T) => React.ReactNode
  sortable?: boolean
  sortAccessor?: (row: T) => string | number | null | undefined
}

interface DataTableProps<T> {
  columns: Column<T>[]
  rows: T[]
  onRowClick?: (row: T) => void
}

export function DataTable<T extends object>({ columns, rows, onRowClick }: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null)
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc")

  const sortedRows = useMemo(() => {
    if (!sortKey) return rows
    const column = columns.find(c => String(c.key) === sortKey)
    if (!column) return rows

    const readValue = (row: T): string | number => {
      const raw = column.sortAccessor ? column.sortAccessor(row) : (row as Record<string, unknown>)[sortKey]
      if (raw === null || raw === undefined) return ""
      if (typeof raw === "number") return raw
      const text = String(raw)
      const maybeDate = Date.parse(text)
      if (!Number.isNaN(maybeDate) && (text.includes("-") || text.includes(":") || text.includes("T") || text.includes("Z"))) {
        return maybeDate
      }
      return text.toLowerCase()
    }

    return [...rows].sort((a, b) => {
      const va = readValue(a)
      const vb = readValue(b)
      if (typeof va === "number" && typeof vb === "number") {
        return sortDir === "asc" ? va - vb : vb - va
      }
      const cmp = String(va).localeCompare(String(vb), undefined, { numeric: true, sensitivity: "base" })
      return sortDir === "asc" ? cmp : -cmp
    })
  }, [rows, columns, sortKey, sortDir])

  const handleSort = (key: string, sortable?: boolean) => {
    if (!sortable) return
    if (sortKey === key) {
      setSortDir(prev => (prev === "asc" ? "desc" : "asc"))
      return
    }
    setSortKey(key)
    setSortDir("desc")
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-800">
            {columns.map(col => (
              <th
                key={String(col.key)}
                className="text-left py-2 px-3 text-gray-400 font-medium"
              >
                <button
                  type="button"
                  onClick={() => handleSort(String(col.key), col.sortable)}
                  className={col.sortable ? "inline-flex items-center gap-1 hover:text-gray-200 transition-colors" : "inline-flex items-center gap-1"}
                >
                  {col.label}
                  {col.sortable && sortKey === String(col.key) && (
                    <span className="text-[10px]">{sortDir === "asc" ? "▲" : "▼"}</span>
                  )}
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((row, i) => (
            <tr
              key={i}
              className={`border-b border-gray-800/50 transition-colors ${onRowClick ? "cursor-pointer hover:bg-gray-800/40" : ""}`}
              onClick={() => onRowClick?.(row)}
            >
              {columns.map(col => (
                <td key={String(col.key)} className="py-2 px-3 text-gray-200">
                  {col.render ? col.render(row) : String((row as Record<string, unknown>)[String(col.key)] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {sortedRows.length === 0 && (
        <p className="text-center py-8 text-gray-500">No data</p>
      )}
    </div>
  )
}
