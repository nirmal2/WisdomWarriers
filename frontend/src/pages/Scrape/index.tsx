import { useEffect, useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { fetchProfilesSource, fetchScrapeStatus, triggerCombinedScrape, updateProfilesSource } from "../../api/scrape"
import { RecentRunsTable } from "../Dashboard/RecentRunsTable"

function parseUsernames(value: string) {
  return Array.from(new Set(value.split(/\r?\n/).map(line => line.trim()).filter(Boolean)))
}

export default function ScrapePage() {
  const qc = useQueryClient()
  const { data } = useQuery({ queryKey: ["profiles-source"], queryFn: fetchProfilesSource })
  const [profilesText, setProfilesText] = useState("")
  const [activeRunId, setActiveRunId] = useState<number | undefined>(undefined)
  const [liveLogs, setLiveLogs] = useState<string[]>([])
  const [showPostsModal, setShowPostsModal] = useState(false)
  const [resultsLimit, setResultsLimit] = useState(100)
  const [newerThanValue, setNewerThanValue] = useState("")
  const [dataDetailLevel, setDataDetailLevel] = useState<"basicData" | "detailedData">("basicData")
  const [batchMode, setBatchMode] = useState(true)
  const [enableEmbeddings, setEnableEmbeddings] = useState(true)
  const usernames = parseUsernames(profilesText)

  const { data: statusData } = useQuery({
    queryKey: ["scrape-status", activeRunId],
    queryFn: () => fetchScrapeStatus(activeRunId),
    refetchInterval: 2000,
  })

  const secondPostScraperCount = statusData?.run?.scraper_type === "posts"
    ? statusData.run.items_fetched
    : (statusData?.db_updates.posts_rows ?? 0)

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

  const handleCombinedScrape = async () => {
    setShowPostsModal(false)
    setLiveLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Saving profiles and starting combined scrape...`].slice(-30))
    try {
      // First save profiles
      const saved = await updateProfilesSource(usernames)
      setProfilesText(saved.usernames.join("\n"))
      qc.invalidateQueries({ queryKey: ["profiles-source"] })
      
      // Then start combined scrape
      setLiveLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Starting combined scrape (Profiles → Posts) for ${saved.usernames.length} profile(s)...`].slice(-30))
      const req: Parameters<typeof triggerCombinedScrape>[0] = {
        usernames: saved.usernames,
        batch_mode: batchMode,
        results_limit: resultsLimit,
        data_detail_level: dataDetailLevel,
        enable_embeddings: enableEmbeddings,
      }
      if (newerThanValue.trim()) {
        req.only_posts_newer_than = newerThanValue.trim()
      }
      await triggerCombinedScrape(req)
      setActiveRunId(undefined)
      qc.invalidateQueries({ queryKey: ["scrape-status"] })
      qc.invalidateQueries({ queryKey: ["runs"] })
    } catch {
      setLiveLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Error during save or scrape`].slice(-30))
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
              <p className="text-xs text-gray-400 mt-1">Configure profile & post scrape parameters. Profiles will be saved and scraped first, then posts.</p>
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
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-gray-300">Only posts newer than (optional)</label>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    placeholder="e.g. 15 days"
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
                {newerThanValue !== "" && (
                  <p className="text-xs text-gray-500">
                    Sent as: <span className="font-mono">{newerThanValue}</span>
                  </p>
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
                <label className="text-xs font-medium text-gray-300">Profile send mode</label>
                <select
                  value={batchMode ? "batch" : "single"}
                  onChange={e => setBatchMode(e.target.value === "batch")}
                  className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100 outline-none focus:border-blue-500"
                >
                  <option value="single">Send one profile per Apify call (safer)</option>
                  <option value="batch">Send all profiles in one batch call (faster)</option>
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
                disabled={!resultsLimit || resultsLimit < 1}
                className="px-4 py-2 text-sm rounded-lg bg-gradient-to-r from-fuchsia-600 to-blue-600 hover:from-fuchsia-500 hover:to-blue-500 text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
              >
                Scrape Now
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
          <span>Profiles will be saved and scraped when you click 'Scrape Wisdom Warriors'.</span>
          <span>Removes duplicates automatically.</span>
        </div>
        <div className="flex justify-center pt-2">
          <button
            onClick={() => setShowPostsModal(true)}
            className="px-3 py-1.5 text-xs bg-fuchsia-600 hover:bg-fuchsia-500 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
            disabled={usernames.length === 0}
          >
            🧙 Scrape Wisdom Warriors
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