import { useEffect, useState, type Dispatch, type SetStateAction } from "react"
import type { PostQueryParams } from "../../types/post"

const DEFAULT_HASHTAGS = [
  "Isha",
  "Ishafoundation",
  "Ishayogacenter",
  "Sadhguru",
  "Sadhgurujaggivasudev",
  "Jaggi",
  "Adiyogi",
  "Linga Bhairavi",
  "Adiyogishiva",
  "ஈஷா",
]

const DEFAULT_MENTIONS = [
  "ishafoundation",
  "adiyogi.official",
  "sadhguru",
  "sadhgurutamil",
  "sadhgurutelugu",
  "sadhguru.hindiofficial",
  "sadhguru.malayalam",
  "sadhguru_marathi_official",
  "sadhgurubangla",
  "sadhguru_kannada_official",
]

const DEFAULT_KEYWORDS = [
  "Isha",
  "Ishafoundation",
  "Ishayogacenter",
  "Sadhguru",
  "Sadhgurujaggivasudev",
  "Jaggi",
  "Adiyogi",
  "Linga Bhairavi",
  "Adiyogishiva",
  "ஈஷா",
  "ईशा",
  "ఇషా",
  "ഇഷ",
  "ಇಶಾ",
  "சத்குரு",
  "సద్గురు",
  "ಸದ್ಗುರು",
  "സദ്‍ഗുരു",
  "सद्गुरु",
]

interface FiltersProps {
  onFilter: (params: PostQueryParams) => void
}

const POSTS_FILTERS_STORAGE_KEY = "insta-analytics.posts.filter-lists"

type PersistedPostFilterLists = {
  hashtags?: string[]
  mentions?: string[]
  keywords?: string[]
}

function getStoredFilterList(key: keyof PersistedPostFilterLists, fallback: string[]) {
  if (typeof window === "undefined") return fallback

  try {
    const raw = window.localStorage.getItem(POSTS_FILTERS_STORAGE_KEY)
    if (!raw) return fallback

    const parsed = JSON.parse(raw) as PersistedPostFilterLists
    const values = parsed[key]
    if (!Array.isArray(values)) return fallback

    const cleaned = values
      .filter((value): value is string => typeof value === "string")
      .map(value => value.trim())
      .filter(Boolean)

    return Array.from(new Set(cleaned))
  } catch {
    return fallback
  }
}

function addFilterValue(value: string, setter: Dispatch<SetStateAction<string[]>>) {
  const normalized = value.trim()
  if (!normalized) return
  setter(prev => (prev.some(item => item.toLowerCase() === normalized.toLowerCase()) ? prev : [...prev, normalized]))
}

function removeFilterValue(value: string, setter: Dispatch<SetStateAction<string[]>>) {
  setter(prev => prev.filter(item => item !== value))
}

export function PostFilters({ onFilter }: FiltersProps) {
  const [username, setUsername] = useState("")
  const [postType, setPostType] = useState("")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [likesMin, setLikesMin] = useState("")
  const [hashtags, setHashtags] = useState<string[]>(() => getStoredFilterList("hashtags", DEFAULT_HASHTAGS))
  const [mentions, setMentions] = useState<string[]>(() => getStoredFilterList("mentions", DEFAULT_MENTIONS))
  const [keywords, setKeywords] = useState<string[]>(() => getStoredFilterList("keywords", DEFAULT_KEYWORDS))
  const [newHashtag, setNewHashtag] = useState("")
  const [newMention, setNewMention] = useState("")
  const [newKeyword, setNewKeyword] = useState("")

  const inputClass = "w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200"

  useEffect(() => {
    window.localStorage.setItem(
      POSTS_FILTERS_STORAGE_KEY,
      JSON.stringify({ hashtags, mentions, keywords })
    )
  }, [hashtags, mentions, keywords])

  const apply = () => onFilter({
    username: username.trim() || undefined,
    type: postType.trim() || undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    likes_min: likesMin ? Number(likesMin) : undefined,
    hashtags: hashtags.length ? hashtags : undefined,
    mentions: mentions.length ? mentions : undefined,
    keywords: keywords.length ? keywords : undefined,
  })

  const reset = () => {
    setUsername("")
    setPostType("")
    setDateFrom("")
    setDateTo("")
    setLikesMin("")
    setHashtags(DEFAULT_HASHTAGS)
    setMentions(DEFAULT_MENTIONS)
    setKeywords(DEFAULT_KEYWORDS)
    setNewHashtag("")
    setNewMention("")
    setNewKeyword("")
    onFilter({})
  }

  return (
    <div className="space-y-4 rounded-xl border border-gray-800 bg-gray-950/50 p-4">
      <div>
        <h2 className="text-sm font-semibold text-gray-200">Post Filters</h2>
        <p className="mt-1 text-xs text-gray-400">
          Filter posts by the allowed hashtags, mentions, caption keywords, and date range.
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <div>
          <p className="mb-1 text-xs font-medium text-gray-400">Username</p>
          <input
            placeholder="Username"
            value={username}
            onChange={e => setUsername(e.target.value)}
            className={inputClass}
          />
        </div>
        <div>
          <p className="mb-1 text-xs font-medium text-gray-400">Type</p>
          <input
            placeholder="Type (video, image, sidecar)"
            value={postType}
            onChange={e => setPostType(e.target.value)}
            className={inputClass}
          />
        </div>
        <div>
          <p className="mb-1 text-xs font-medium text-gray-400">From Date</p>
          <input
            type="date"
            value={dateFrom}
            onChange={e => setDateFrom(e.target.value)}
            className={inputClass}
          />
        </div>
        <div>
          <p className="mb-1 text-xs font-medium text-gray-400">To Date</p>
          <input
            type="date"
            value={dateTo}
            onChange={e => setDateTo(e.target.value)}
            className={inputClass}
          />
        </div>
        <div>
          <p className="mb-1 text-xs font-medium text-gray-400">Min Likes</p>
          <input
            placeholder="Min likes"
            type="number"
            value={likesMin}
            onChange={e => setLikesMin(e.target.value)}
            className={inputClass}
          />
        </div>
      </div>

      <div className="grid gap-3 xl:grid-cols-3">
        <div>
          <p className="mb-2 text-xs font-medium text-gray-400">Allowed Hashtags</p>
          <div className="mb-2 flex gap-2">
            <input
              value={newHashtag}
              onChange={e => setNewHashtag(e.target.value)}
              placeholder="Add hashtag"
              className={inputClass}
            />
            <button
              type="button"
              onClick={() => {
                addFilterValue(newHashtag, setHashtags)
                setNewHashtag("")
              }}
              className="rounded-lg border border-gray-700 px-3 py-2 text-xs text-gray-200 hover:bg-gray-800"
            >
              Add
            </button>
          </div>
          <div className="flex flex-wrap gap-1">
            {hashtags.map(value => (
              <button
                key={value}
                type="button"
                onClick={() => removeFilterValue(value, setHashtags)}
                className="inline-flex items-center rounded-full border border-gray-700 bg-gray-900 px-2 py-0.5 text-[11px] text-gray-300 hover:border-red-700 hover:text-red-300"
              >
                {value} ×
              </button>
            ))}
          </div>
        </div>

        <div>
          <p className="mb-2 text-xs font-medium text-gray-400">Allowed Mentions</p>
          <div className="mb-2 flex gap-2">
            <input
              value={newMention}
              onChange={e => setNewMention(e.target.value)}
              placeholder="Add mention"
              className={inputClass}
            />
            <button
              type="button"
              onClick={() => {
                addFilterValue(newMention, setMentions)
                setNewMention("")
              }}
              className="rounded-lg border border-gray-700 px-3 py-2 text-xs text-gray-200 hover:bg-gray-800"
            >
              Add
            </button>
          </div>
          <div className="flex flex-wrap gap-1">
            {mentions.map(value => (
              <button
                key={value}
                type="button"
                onClick={() => removeFilterValue(value, setMentions)}
                className="inline-flex items-center rounded-full border border-gray-700 bg-gray-900 px-2 py-0.5 text-[11px] text-gray-300 hover:border-red-700 hover:text-red-300"
              >
                {value} ×
              </button>
            ))}
          </div>
        </div>

        <div>
          <p className="mb-2 text-xs font-medium text-gray-400">Allowed Caption Keywords</p>
          <div className="mb-2 flex gap-2">
            <input
              value={newKeyword}
              onChange={e => setNewKeyword(e.target.value)}
              placeholder="Add keyword"
              className={inputClass}
            />
            <button
              type="button"
              onClick={() => {
                addFilterValue(newKeyword, setKeywords)
                setNewKeyword("")
              }}
              className="rounded-lg border border-gray-700 px-3 py-2 text-xs text-gray-200 hover:bg-gray-800"
            >
              Add
            </button>
          </div>
          <div className="flex flex-wrap gap-1">
            {keywords.map(value => (
              <button
                key={value}
                type="button"
                onClick={() => removeFilterValue(value, setKeywords)}
                className="inline-flex items-center rounded-full border border-gray-700 bg-gray-900 px-2 py-0.5 text-[11px] text-gray-300 hover:border-red-700 hover:text-red-300"
              >
                {value} ×
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-end gap-2">
        <button
          type="button"
          onClick={reset}
          className="rounded-lg border border-gray-700 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-800"
        >
          Reset
        </button>
        <button
          type="button"
          onClick={apply}
          className="rounded-lg bg-blue-700 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-600"
        >
          Apply
        </button>
      </div>
    </div>
  )
}
