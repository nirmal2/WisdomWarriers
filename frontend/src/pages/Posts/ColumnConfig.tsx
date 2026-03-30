import { useState } from "react"

interface ColumnConfiguratorProps {
  availableColumns: {
    key: string
    label: string
  }[]
  selectedColumns: Set<string>
  onColumnsChange: (columns: Set<string>) => void
}

export function ColumnConfigurator({ availableColumns, selectedColumns, onColumnsChange }: ColumnConfiguratorProps) {
  const [isOpen, setIsOpen] = useState(false)

  const handleToggle = (key: string) => {
    const newSelected = new Set(selectedColumns)
    if (newSelected.has(key)) {
      newSelected.delete(key)
    } else {
      newSelected.add(key)
    }
    onColumnsChange(newSelected)
  }

  const handleSelectAll = () => {
    onColumnsChange(new Set(availableColumns.map(c => c.key)))
  }

  const handleClearAll = () => {
    onColumnsChange(new Set())
  }

  return (
    <div className="relative inline-block">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="px-3 py-1.5 text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 rounded border border-gray-700 transition-colors"
      >
        Columns ({selectedColumns.size}/{availableColumns.length})
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute top-full right-0 mt-2 w-56 bg-gray-900 border border-gray-700 rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
            <div className="sticky top-0 bg-gray-900 border-b border-gray-700 px-3 py-2 flex gap-2">
              <button
                onClick={handleSelectAll}
                className="text-xs px-2 py-1 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded"
              >
                All
              </button>
              <button
                onClick={handleClearAll}
                className="text-xs px-2 py-1 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded"
              >
                None
              </button>
            </div>
            <div className="px-3 py-2 space-y-2">
              {availableColumns.map(col => (
                <label key={col.key} className="flex items-center gap-2 cursor-pointer hover:bg-gray-800/50 px-2 py-1 rounded">
                  <input
                    type="checkbox"
                    checked={selectedColumns.has(col.key)}
                    onChange={() => handleToggle(col.key)}
                    className="w-4 h-4 rounded border-gray-600 accent-blue-500 cursor-pointer"
                  />
                  <span className="text-xs text-gray-300">{col.label}</span>
                </label>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
