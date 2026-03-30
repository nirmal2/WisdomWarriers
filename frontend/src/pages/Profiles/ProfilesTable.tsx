import type { Profile } from "../../types/profile"
import { useNavigate } from "react-router-dom"

const compact = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 })
const fmt = (n: number) => compact.format(n)
const avatarFallback = (username: string) =>
  `data:image/svg+xml;utf8,${encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
      <rect width="128" height="128" rx="64" fill="#e2e8f0" />
      <text x="50%" y="54%" dominant-baseline="middle" text-anchor="middle" font-family="Arial, sans-serif" font-size="52" font-weight="700" fill="#475569">${username.slice(0, 1).toUpperCase()}</text>
    </svg>`,
  )}`

const THEME = {
  banner: "from-indigo-500 to-violet-600",
  ring: "ring-indigo-300",
  accent: "text-indigo-500",
  btn: "bg-gradient-to-r from-indigo-500 to-violet-600 hover:from-indigo-400 hover:to-violet-500",
  statAccent: "text-indigo-500",
}

export function ProfilesTable({ profiles }: { profiles: Profile[] }) {
  const nav = useNavigate()

  if (profiles.length === 0)
    return <p className="py-10 text-center text-sm text-gray-500">No profiles found</p>

  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
      {profiles.map(profile => {
        const t = THEME
        const bioText = profile.biography || profile.business_category || "No biography available."
        return (
          <article
            key={profile.id}
            className="group flex min-h-[29rem] flex-col overflow-hidden rounded-3xl bg-white text-slate-900 shadow-md ring-1 ring-black/5 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl sm:min-h-[30rem]"
          >
            {/* Banner */}
            <div className={`h-24 bg-gradient-to-br ${t.banner}`} />

            {/* Body */}
            <div className="flex flex-1 flex-col px-4 pb-4 pt-2 sm:px-5 sm:pb-5">
              {/* Avatar + CTA */}
              <div className="-mt-12 mb-4 flex flex-col items-center gap-2.5 sm:-mt-14 sm:gap-3">
                {profile.profile_pic_url ? (
                  <img
                    src={profile.profile_pic_url}
                    alt={profile.username}
                    className={`h-20 w-20 rounded-full border-[4px] border-white object-cover shadow-md ring-2 ${t.ring} sm:h-24 sm:w-24`}
                    loading="lazy"
                    onError={event => {
                      event.currentTarget.onerror = null
                      event.currentTarget.src = avatarFallback(profile.username)
                    }}
                  />
                ) : (
                  <div className={`flex h-20 w-20 items-center justify-center rounded-full border-[4px] border-white bg-slate-100 text-[clamp(1.2rem,2.4vw,1.6rem)] font-bold text-slate-600 shadow-md ring-2 ${t.ring} sm:h-24 sm:w-24`}>
                    {profile.username.slice(0, 1).toUpperCase()}
                  </div>
                )}
                <button
                  type="button"
                  onClick={() => nav(`/profiles/${profile.username}`)}
                  className={`rounded-full px-5 py-2 text-[clamp(0.9rem,1vw,1.08rem)] font-semibold text-white shadow-sm transition-all ${t.btn}`}
                >
                  View Profile
                </button>
              </div>

              {/* Name + handle */}
              <div className="mb-3 text-center">
                <div className="flex min-h-[3.25rem] items-start justify-center gap-1 text-center text-[clamp(1.15rem,1.35vw,1.9rem)] font-bold leading-snug text-slate-800 sm:min-h-[3.5rem]">
                  <span className="line-clamp-2 break-words">{profile.full_name || profile.username}</span>
                  {profile.is_verified && <span className={`mt-1 shrink-0 text-[clamp(0.8rem,0.9vw,1rem)] ${t.accent}`}>✓</span>}
                </div>
                <p className="mt-1 break-all text-[clamp(0.92rem,0.95vw,1.05rem)] text-slate-500">@{profile.username}</p>
              </div>

              {/* Bio */}
              <p
                className="mb-5 line-clamp-4 min-h-[5.8rem] break-words text-center text-[clamp(0.82rem,0.84vw,0.95rem)] leading-[1.6] text-slate-600 sm:min-h-[6.5rem]"
                title={bioText}
              >
                {bioText}
              </p>

              {/* Stats strip */}
              <div className="mt-auto rounded-xl bg-slate-50 px-2.5 py-3 ring-1 ring-slate-100 sm:px-3">
                <div className="grid grid-cols-4 divide-x divide-slate-200 text-center">
                  {[
                    { value: fmt(profile.followers_count), label: "Followers", colored: false, href: undefined, internalTo: undefined },
                    { value: fmt(profile.posts_count),     label: "Posts",     colored: true,  href: profile.url, internalTo: undefined },
                    { value: fmt(profile.follows_count),   label: "Following", colored: false, href: undefined, internalTo: undefined },
                    { value: String(profile.highlight_reel_count), label: "#Tagged", colored: true, href: undefined, internalTo: `/profiles/${profile.username}/tagged-posts` },
                  ].map(({ value, label, colored, href, internalTo }) => (
                    <div key={label} className="min-w-0 px-1">
                      {href || internalTo ? (
                        <a
                          href={href || internalTo}
                          target={href ? "_blank" : undefined}
                          rel={href ? "noreferrer" : undefined}
                          onClick={event => {
                            if (internalTo) {
                              event.preventDefault()
                              nav(internalTo)
                            }
                          }}
                          className="block rounded-lg transition-opacity hover:opacity-80"
                        >
                          <p className={`truncate text-[clamp(1rem,1.2vw,1.6rem)] font-bold leading-none tabular-nums ${colored ? t.statAccent : "text-slate-800"}`}>
                            {value}
                          </p>
                          <p className="mt-2 text-[clamp(0.55rem,0.6vw,0.7rem)] font-semibold uppercase tracking-[0.12em] text-slate-400">
                            {label}
                          </p>
                        </a>
                      ) : (
                        <>
                          <p className={`truncate text-[clamp(1rem,1.2vw,1.6rem)] font-bold leading-none tabular-nums ${colored ? t.statAccent : "text-slate-800"}`}>
                            {value}
                          </p>
                          <p className="mt-2 text-[clamp(0.55rem,0.6vw,0.7rem)] font-semibold uppercase tracking-[0.12em] text-slate-400">
                            {label}
                          </p>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </article>
        )
      })}
    </div>
  )
}
