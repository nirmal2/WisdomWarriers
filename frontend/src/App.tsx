import { useEffect, useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { BrowserRouter, Routes, Route, NavLink, useLocation } from "react-router-dom"
import { LayoutDashboard, Users, FileText, CalendarClock, MessageSquare, Search, ShieldCheck, ChevronDown, ChevronRight, GitCompare, Swords } from "lucide-react"
import { clsx } from "clsx"
import DashboardPage from "./pages/Dashboard"
import ProfilesPage from "./pages/Profiles"
import { ProfileDetail } from "./pages/Profiles/ProfileDetail"
import { TaggedPostsPage } from "./pages/Profiles/TaggedPostsPage"
import PostsPage from "./pages/Posts"
import SchedulesPage from "./pages/Schedules"
import ChatPage from "./pages/Chat"
import ScrapePage from "./pages/Scrape"
import CompareRunsPage from "./pages/CompareRuns"
import WisdomWarriorsPage from "./pages/WisdomWarriors"
import { fetchScrapeStatus } from "./api/scrape"
import { fetchWisdomWarriorsSnapshotRuns, type WisdomWarriorSnapshotRun } from "./api/wisdomWarriors"

const NAV = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard", end: true },
  { to: "/wisdom-warriors", icon: Swords, label: "Wisdom Warriors" },
  { to: "/profiles", icon: Users, label: "Profiles" },
  { to: "/posts", icon: FileText, label: "Posts" },
  { to: "/chat", icon: MessageSquare, label: "AI Chat" },
]

const ADMIN_NAV = [
  { to: "/scrape-instagram", icon: Search, label: "Wisdom Warriors Scraper" },
  { to: "/scrape-instagram/hashtag-scraper", icon: Search, label: "Hashtag Scraper" },
  { to: "/scrape-instagram/mentions-scraper", icon: Search, label: "Mentions Scraper" },
  { to: "/scrape-youtube", icon: Search, label: "YouTube Scraper" },
  { to: "/scrape-facebook", icon: Search, label: "Facebook Scraper" },
  { to: "/compare-runs", icon: GitCompare, label: "Compare Runs" },
  { to: "/schedules", icon: CalendarClock, label: "Schedules" },
]

function Sidebar() {
  const location = useLocation()
  const adminActive = ADMIN_NAV.some(item => location.pathname.startsWith(item.to))
  const [adminOpen, setAdminOpen] = useState(adminActive)

  return (
    <aside className="w-56 flex-shrink-0 border-r border-gray-800 flex flex-col py-6 px-3 gap-1">
      <div className="px-3 mb-6">
        <span className="text-lg font-bold text-white tracking-tight">Wisdom Warriors - Analytics</span>
      </div>
      {NAV.map(({ to, icon: Icon, label, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            clsx(
              "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
              isActive
                ? "bg-purple-800 text-white"
                : "text-gray-400 hover:text-white hover:bg-gray-800"
            )
          }
        >
          <Icon size={16} />
          {label}
        </NavLink>
      ))}

      {/* Admin group */}
      <div className="mt-1">
        <button
          onClick={() => setAdminOpen(o => !o)}
          className={clsx(
            "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
            adminActive
              ? "text-white"
              : "text-gray-400 hover:text-white hover:bg-gray-800"
          )}
        >
          <ShieldCheck size={16} />
          <span className="flex-1 text-left">Admin</span>
          {adminOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </button>
        {adminOpen && (
          <div className="ml-4 mt-0.5 flex flex-col gap-0.5 border-l border-gray-800 pl-2">
            <div className="px-3 py-1 text-[11px] uppercase tracking-wide text-gray-500">Instagram Scraper</div>
            {ADMIN_NAV.filter(item => item.to.startsWith("/scrape-instagram")).map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  clsx(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                    isActive
                      ? "bg-purple-800 text-white"
                      : "text-gray-400 hover:text-white hover:bg-gray-800"
                  )
                }
              >
                <Icon size={16} />
                {label}
              </NavLink>
            ))}

            <div className="px-3 py-1 text-[11px] uppercase tracking-wide text-gray-500">YouTube Scraper</div>
            {ADMIN_NAV.filter(item => item.to === "/scrape-youtube").map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  clsx(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                    isActive
                      ? "bg-purple-800 text-white"
                      : "text-gray-400 hover:text-white hover:bg-gray-800"
                  )
                }
              >
                <Icon size={16} />
                {label}
              </NavLink>
            ))}

            <div className="px-3 py-1 text-[11px] uppercase tracking-wide text-gray-500">Facebook Scraper</div>
            {ADMIN_NAV.filter(item => item.to === "/scrape-facebook").map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  clsx(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                    isActive
                      ? "bg-purple-800 text-white"
                      : "text-gray-400 hover:text-white hover:bg-gray-800"
                  )
                }
              >
                <Icon size={16} />
                {label}
              </NavLink>
            ))}

            <div className="px-3 py-1 text-[11px] uppercase tracking-wide text-gray-500">Admin Tools</div>
            {ADMIN_NAV.filter(item => !item.to.startsWith("/scrape-instagram") && item.to !== "/scrape-youtube" && item.to !== "/scrape-facebook").map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  clsx(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                    isActive
                      ? "bg-purple-800 text-white"
                      : "text-gray-400 hover:text-white hover:bg-gray-800"
                  )
                }
              >
                <Icon size={16} />
                {label}
              </NavLink>
            ))}
          </div>
        )}
      </div>
    </aside>
  )
}

export default function App() {
  const [selectedSnapshotRunId, setSelectedSnapshotRunId] = useState<number | undefined>(undefined)

  const { data: scrapeStatus } = useQuery({
    queryKey: ["global-last-scrape"],
    queryFn: () => fetchScrapeStatus(),
    refetchInterval: 15000,
  })

  const { data: snapshotRuns = [] } = useQuery({
    queryKey: ["global-snapshot-runs"],
    queryFn: () => fetchWisdomWarriorsSnapshotRuns(),
    refetchInterval: 30000,
  })

  useEffect(() => {
    if (selectedSnapshotRunId !== undefined) return
    if (snapshotRuns.length === 0) return
    setSelectedSnapshotRunId(snapshotRuns[0].run_id)
  }, [selectedSnapshotRunId, snapshotRuns])

  const selectedSnapshotRun = useMemo(
    () => snapshotRuns.find(run => run.run_id === selectedSnapshotRunId),
    [snapshotRuns, selectedSnapshotRunId]
  )

  const lastScrapedAt = scrapeStatus?.run?.finished_at ?? scrapeStatus?.run?.started_at
  const fallbackLastScrapedLabel = lastScrapedAt
    ? new Date(lastScrapedAt).toLocaleString()
    : "Not available"

  const selectedScrapedLabel = selectedSnapshotRun?.scraped_at
    ? new Date(selectedSnapshotRun.scraped_at).toLocaleString()
    : fallbackLastScrapedLabel

  return (
    <BrowserRouter>
      <div className="flex h-screen bg-gray-950 text-gray-100 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto pr-4 md:pr-6 lg:pr-8">
          <div className="sticky top-0 z-10 border-b border-gray-800 bg-gray-950/95 backdrop-blur px-4 py-2 text-xs text-gray-300">
            <div className="flex items-center gap-2">
              <label htmlFor="global-scraped-at" className="text-gray-300">Last scraped at:</label>
              <select
                id="global-scraped-at"
                value={selectedSnapshotRunId ?? ""}
                onChange={e => {
                  const value = e.target.value
                  setSelectedSnapshotRunId(value ? Number(value) : undefined)
                }}
                className="min-w-[240px] rounded border border-gray-700 bg-gray-900 px-2 py-1 text-xs text-gray-100"
                disabled={snapshotRuns.length === 0}
              >
                {snapshotRuns.length === 0 && <option value="">{selectedScrapedLabel}</option>}
                {snapshotRuns.map((run: WisdomWarriorSnapshotRun) => (
                  <option key={run.run_id} value={run.run_id}>
                    {new Date(run.scraped_at).toLocaleString()}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <Routes>
            <Route
              path="/"
              element={
                <DashboardPage
                  selectedSnapshotRunId={selectedSnapshotRunId}
                  selectedScrapedAt={selectedSnapshotRun?.scraped_at}
                />
              }
            />
            <Route path="/wisdom-warriors" element={<WisdomWarriorsPage selectedSnapshotRunId={selectedSnapshotRunId} />} />
            <Route path="/scrape-instagram" element={<ScrapePage />} />
            <Route path="/scrape-instagram/hashtag-scraper" element={<ScrapePage />} />
            <Route path="/scrape-instagram/mentions-scraper" element={<ScrapePage />} />
            <Route path="/scrape-youtube" element={<ScrapePage />} />
            <Route path="/scrape-facebook" element={<ScrapePage />} />
            <Route path="/compare-runs" element={<CompareRunsPage />} />
            <Route path="/profiles" element={<ProfilesPage />} />
            <Route path="/profiles/:username" element={<ProfileDetail />} />
            <Route path="/profiles/:username/tagged-posts" element={<TaggedPostsPage />} />
            <Route path="/posts" element={<PostsPage selectedSnapshotRunId={selectedSnapshotRunId} />} />
            <Route path="/schedules" element={<SchedulesPage />} />
            <Route path="/chat" element={<ChatPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
