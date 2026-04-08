import { useEffect, useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { fetchScrapeStatus, triggerCombinedScrape, triggerScrape } from "../../api/scrape"
import { fetchProfileUsernames } from "../../api/profiles"
import { RecentRunsTable } from "../Dashboard/RecentRunsTable"

function parseUsernames(value: string) {
  return Array.from(new Set(value.split(/\r?\n/).map(line => line.trim()).filter(Boolean)))
}

const APIFY_TOKEN_STORAGE_KEY = "wisdom-warriors.apify-token"
const MS_PER_DAY = 24 * 60 * 60 * 1000

function getDerivedDaysValue(daysValue: string, dateFrom: string) {
  const trimmed = daysValue.trim()
  if (trimmed) return trimmed
  if (!dateFrom) return ""

  const from = new Date(`${dateFrom}T00:00:00`)
  if (Number.isNaN(from.getTime())) return ""

  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  return String(Math.max(0, Math.ceil((today.getTime() - from.getTime()) / MS_PER_DAY)))
}

export default function ScrapePage() {
  const qc = useQueryClient()
  const { data } = useQuery({ queryKey: ["profile-usernames"], queryFn: fetchProfileUsernames })
  const [profilesText, setProfilesText] = useState("")
  const [activeRunId, setActiveRunId] = useState<number | undefined>(undefined)
  const [liveLogs, setLiveLogs] = useState<string[]>([])
  const [showPostsModal, setShowPostsModal] = useState(false)
  const [resultsLimit, setResultsLimit] = useState(100)
  const [newerThanValue, setNewerThanValue] = useState("")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [dataDetailLevel, setDataDetailLevel] = useState<"basicData" | "detailedData">("basicData")
  const [includeProfileScrape, setIncludeProfileScrape] = useState(false)
  const [batchMode, setBatchMode] = useState(true)
  const [enableEmbeddings, setEnableEmbeddings] = useState(true)
  const [apifyToken, setApifyToken] = useState("")
  const [isScrapeLocked, setIsScrapeLocked] = useState(false)
  const usernames = parseUsernames(profilesText)

  const { data: statusData } = useQuery({
    queryKey: ["scrape-status", activeRunId],
    queryFn: () => fetchScrapeStatus(activeRunId),
    refetchInterval: 2000,
  })

  const secondPostScraperCount = statusData?.run?.scraper_type === "posts"
    ? statusData.run.items_fetched
    : (statusData?.db_updates.posts_rows ?? 0)
  const currentRunStatus = statusData?.run?.status
  const isScrapeBusy = isScrapeLocked || currentRunStatus === "running"
  const hasInvalidDateRange = Boolean(dateFrom && dateTo && dateFrom > dateTo)
  const effectiveDaysValue = getDerivedDaysValue(newerThanValue, dateFrom)

  useEffect(() => {
    if (!statusData?.run) return
    setActiveRunId(prev => prev ?? statusData.run?.id)
  }, [statusData])

  useEffect(() => {
    if (!statusData) return
    const timestamp = new Date().toLocaleTimeString()
    setLiveLogs(prev => {
      const next = [...prev]
      for (const line of statusData.logs) {
        const alreadyExists = next.some(existing => existing.endsWith(`] ${line}`))
        if (!alreadyExists) next.push(`[${timestamp}] ${line}`)
      }
      return next.slice(-120)
    })
  }, [statusData])

  useEffect(() => {
    if (data) {
      setProfilesText(data.usernames.join("\n"))
    }
  }, [data])

  useEffect(() => {
    const storedToken = window.localStorage.getItem(APIFY_TOKEN_STORAGE_KEY)
    if (storedToken) setApifyToken(storedToken)
  }, [])

  useEffect(() => {
    if (!isScrapeLocked) return
    if (currentRunStatus === "completed" || currentRunStatus === "failed") {
      setIsScrapeLocked(false)
    }
  }, [currentRunStatus, isScrapeLocked])

  useEffect(() => {
    const trimmed = apifyToken.trim()
    if (trimmed) {
      window.localStorage.setItem(APIFY_TOKEN_STORAGE_KEY, trimmed)
    } else {
      window.localStorage.removeItem(APIFY_TOKEN_STORAGE_KEY)
    }
  }, [apifyToken])

  const handleCombinedScrape = async () => {
    if (isScrapeBusy || usernames.length === 0 || hasInvalidDateRange) return

    const startedAt = new Date().toLocaleTimeString()
    const modeLabel = includeProfileScrape ? "combined scrape" : "posts-only scrape"
    setIsScrapeLocked(true)
    setLiveLogs([
      `[${startedAt}] Starting ${modeLabel}...`,
      `[${startedAt}] Submitting ${usernames.length} profile(s) for scraping...`,
    ])
    try {
      const req: Parameters<typeof triggerCombinedScrape>[0] = {
        usernames: usernames,
        batch_mode: batchMode,
        results_limit: resultsLimit,
        data_detail_level: dataDetailLevel,
        enable_embeddings: enableEmbeddings,
      }
      if (effectiveDaysValue) {
        req.only_posts_newer_than = effectiveDaysValue
      }
      if (dateFrom) {
        req.date_from = dateFrom
      }
      if (dateTo) {
        req.date_to = dateTo
      }
      if (apifyToken.trim()) {
        req.apify_token = apifyToken.trim()
      }
      const started = includeProfileScrape
        ? await triggerCombinedScrape(req)
        : await triggerScrape({ ...req, scraper_type: "posts" })
      setActiveRunId(started.run_id)
      setShowPostsModal(false)
      setLiveLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Tracking run #${started.run_id}.`].slice(-120))
      qc.invalidateQueries({ queryKey: ["scrape-status", started.run_id] })
      qc.invalidateQueries({ queryKey: ["runs"] })
    } catch {
      setIsScrapeLocked(false)
      setLiveLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Error while starting scrape.`].slice(-120))
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Wisdom Warriors Scraper</h1>
          <p className="text-sm text-gray-400 mt-1">Manage the usernames to scrape and monitor each scrape run.</p>
        </div>
      </div>
      {showPostsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-gray-700 bg-gray-900 p-6 shadow-2xl space-y-5">
            <div>
              <h2 className="text-base font-semibold text-gray-100">Scrape Wisdom Warriors</h2>
              <p className="text-xs text-gray-400 mt-1">Configure the post scrape. Profile scraping is optional and is off by default.</p>
            </div>
            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-gray-300">Max posts per profile <span className="text-red-400">*</span></label>
                <input
                  type="number"
                  min={1}
                  max={500}
                  value={resultsLimit}
                  onChange={e => setResultsLimit(Number(e.target.value))}
                  className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 outline-none focus:border-blue-500"
                />
              </div>
              <div className="space-y-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-gray-300">Days (optional)</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      min={0}
                      placeholder="e.g. 15"
                      value={newerThanValue}
                      onChange={e => setNewerThanValue(e.target.value)}
                      className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 outline-none focus:border-blue-500"
                    />
                    {newerThanValue !== "" && (
                      <button
                        onClick={() => setNewerThanValue("")}
                        className="text-gray-500 hover:text-gray-300 text-sm leading-none px-1"
                        title="Clear"
                      >✕</button>
                    )}
                  </div>
                </div>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-gray-300">From</label>
                    <input
                      type="date"
                      value={dateFrom}
                      onChange={e => setDateFrom(e.target.value)}
                      className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 outline-none focus:border-blue-500"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-gray-300">To</label>
                    <input
                      type="date"
                      value={dateTo}
                      min={dateFrom || undefined}
                      onChange={e => setDateTo(e.target.value)}
                      className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 outline-none focus:border-blue-500"
                    />
                  </div>
                </div>
                <p className="text-xs text-gray-500">
                  Use Days, From, To, or both. The date range is applied exactly after scraping, and Days limits the fetch window.
                </p>
                {effectiveDaysValue !== "" && (
                  <p className="text-xs text-gray-500">
                    Sent as: <span className="font-mono">{effectiveDaysValue} days</span>
                  </p>
                )}
                {hasInvalidDateRange && (
                  <p className="text-xs text-red-400">The To date must be on or after the From date.</p>
                )}
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-gray-300">Data detail level <span className="text-red-400">*</span></label>
                <select
                  value={dataDetailLevel}
                  onChange={e => setDataDetailLevel(e.target.value as "basicData" | "detailedData")}
                  className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 outline-none focus:border-blue-500"
                >
                  <option value="basicData">Basic data (faster, cheaper)</option>
                  <option value="detailedData">Detailed data (includes video play count, alt text, music info)</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-gray-300">APIFY token override (optional)</label>
                <input
                  type="password"
                  placeholder="Leave blank to use the backend default token"
                  value={apifyToken}
                  onChange={e => setApifyToken(e.target.value)}
                  className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 outline-none focus:border-blue-500"
                />
                <p className="text-xs text-gray-500">
                  This value is stored only in this browser for Admin convenience and is used for manual Wisdom Warriors scrapes.
                </p>
              </div>
              <label className="flex items-start gap-3 rounded-lg border border-gray-700 bg-gray-800/60 px-3 py-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeProfileScrape}
                  onChange={e => setIncludeProfileScrape(e.target.checked)}
                  className="mt-0.5 h-4 w-4 rounded border-gray-600 accent-fuchsia-500"
                />
                <span className="space-y-1">
                  <span className="block text-xs font-medium text-gray-300">Scrape profiles before posts</span>
                  <span className="block text-xs text-gray-500">Optional. Leave this off for a faster posts-only scrape.</span>
                </span>
              </label>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-gray-300">Post scraping mode</label>
                <select
                  value={batchMode ? "batch" : "single"}
                  onChange={e => setBatchMode(e.target.value === "batch")}
                  className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 outline-none focus:border-blue-500"
                >
                  <option value="single">Scrape posts one profile at a time (safer)</option>
                  <option value="batch">Scrape posts for all profiles in one batch (faster)</option>
                </select>
              </div>
              <label className="flex items-start gap-3 rounded-lg border border-gray-700 bg-gray-800/60 px-3 py-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={enableEmbeddings}
                  onChange={e => setEnableEmbeddings(e.target.checked)}
                  className="mt-0.5 h-4 w-4 rounded border-gray-600 accent-fuchsia-500"
                />
                <span className="space-y-1">
                  <span className="block text-xs font-medium text-gray-300">Generate embeddings after scrape</span>
                  <span className="block text-xs text-gray-500">Turn this off to scrape and store data without running the embedding/indexing step.</span>
                </span>
              </label>
            </div>
            <div className="flex justify-end gap-2 pt-1">
              <button
                onClick={() => setShowPostsModal(false)}
                className="px-4 py-2 text-sm rounded-lg border border-gray-700 text-gray-300 hover:bg-gray-800 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCombinedScrape}
                disabled={!resultsLimit || resultsLimit < 1 || isScrapeBusy || hasInvalidDateRange}
                className="px-4 py-2 text-sm rounded-lg bg-gradient-to-r from-fuchsia-600 to-blue-600 hover:from-fuchsia-500 hover:to-blue-500 text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
              >
                {isScrapeBusy ? "Scrape in Progress…" : "Scrape Now"}
              </button>
            </div>
          </div>
        </div>
      )}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-5 space-y-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-sm font-semibold text-gray-200">Profiles To Scrape</h2>
            <p className="text-xs text-gray-400 mt-1">Edit the Instagram usernames used by manual scrapes. One profile per line.</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-400">{usernames.length} profiles</span>
          </div>
        </div>
        <textarea
          value={profilesText}
          onChange={e => setProfilesText(e.target.value)}
          className="w-full min-h-72 rounded-xl border border-gray-800 bg-gray-950 px-4 py-3 text-sm text-gray-100 outline-none focus:border-purple-600"
          placeholder="Enter one Instagram username per line"
        />
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>
            {isScrapeBusy
              ? "Scrape in progress. The button will re-enable after the selected stages finish and the database updates complete."
              : "The listed usernames are used for manual scrapes, and profile scraping can be turned on in the popup if needed."}
          </span>
          <span>Removes duplicates automatically.</span>
        </div>
        <div className="flex justify-center pt-2">
          <button
            onClick={() => setShowPostsModal(true)}
            className="px-3 py-1.5 text-xs bg-fuchsia-600 hover:bg-fuchsia-500 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
            disabled={usernames.length === 0 || isScrapeBusy}
          >
            {isScrapeBusy ? "🧙 Scrape in Progress…" : "🧙 Scrape Wisdom Warriors"}
          </button>
        </div>
      </div>
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-5 space-y-4">
        <div>
          <h2 className="text-sm font-semibold text-gray-200">Database Update Status</h2>
          <p className="text-xs text-gray-400 mt-1">Rows updated for the selected run.</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="rounded-lg border border-gray-800 bg-gray-950 p-3">
            <p className="text-xs text-gray-400">Profiles Scraped</p>
            <p className="text-lg font-semibold mt-1">{statusData?.db_updates.profiles_touched ?? 0}</p>
          </div>
          <div className="rounded-lg border border-gray-800 bg-gray-950 p-3">
            <p className="text-xs text-gray-400">Posts (Second Scraper)</p>
            <p className="text-lg font-semibold mt-1">{secondPostScraperCount}</p>
          </div>
        </div>
        <div className="rounded-lg border border-gray-800 bg-gray-950 p-3">
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs text-gray-400">Missing Profiles</p>
            <p className="text-xs text-red-300">{statusData?.db_updates.missing_usernames?.length ?? 0} missing</p>
          </div>
          {statusData?.db_updates.missing_usernames?.length ? (
            <div className="mt-3 flex flex-wrap gap-2">
              {statusData.db_updates.missing_usernames.map(username => (
                <span
                  key={username}
                  className="rounded-full border border-red-900 bg-red-950/60 px-2 py-1 text-xs text-red-200"
                >
                  {username}
                </span>
              ))}
            </div>
          ) : (
            <p className="mt-3 text-sm text-gray-500">No missing profiles for this run.</p>
          )}
        </div>
      </div>
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-5 space-y-4">
        <div>
          <h2 className="text-sm font-semibold text-gray-200">Live Logs</h2>
          <p className="text-xs text-gray-400 mt-1">Real-time run and DB update messages.</p>
        </div>
        <div className="rounded-xl border border-gray-800 bg-gray-950 px-4 py-3 text-xs text-gray-200 font-mono max-h-56 overflow-auto space-y-1">
          {liveLogs.length === 0 ? (
            <div className="text-gray-500">No logs yet. Start a scrape to stream updates.</div>
          ) : (
            liveLogs.map((line, i) => <div key={`${line}-${i}`}>{line}</div>)
          )}
        </div>
      </div>
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-5">
        <h2 className="text-sm font-semibold text-gray-300 mb-4">Recent Scrape Runs</h2>
        <RecentRunsTable />
      </div>
    </div>
  )
}