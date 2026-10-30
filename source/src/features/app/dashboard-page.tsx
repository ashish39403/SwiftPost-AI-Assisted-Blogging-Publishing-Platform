"use client"

import * as React from "react"
import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import {
  ArrowRight,
  ArrowUpRight,
  Bot,
  CheckCircle2,
  Clock3,
  FilePenLine,
  Flame,
  Layers3,
  Rocket,
  Sparkles,
  RefreshCw,
} from "lucide-react"
import { AppShell } from "@/features/app/app-shell"
import { Button } from "@/components/ui/button"
import { accountLabel, api, mediaUrl, type Account, type Paginated, type Post } from "@/lib/api"

const STATUS_STYLE: Record<string, { label: string; color: string; ring: string }> = {
  draft: { label: "Draft", color: "var(--primary)", ring: "color-mix(in oklch, var(--primary) 18%, transparent)" },
  in_review: { label: "In review", color: "var(--highlight)", ring: "color-mix(in oklch, var(--highlight) 18%, transparent)" },
  published: { label: "Published", color: "var(--success)", ring: "color-mix(in oklch, var(--success) 18%, transparent)" },
  changes_requested: { label: "Changes requested", color: "oklch(0.72 0.14 55)", ring: "color-mix(in oklch, oklch(0.72 0.14 55) 18%, transparent)" },
  unpublished: { label: "Unpublished", color: "oklch(0.55 0.04 264)", ring: "color-mix(in oklch, oklch(0.55 0.04 264) 18%, transparent)" },
  archived: { label: "Archived", color: "oklch(0.72 0.02 92)", ring: "color-mix(in oklch, oklch(0.72 0.02 92) 18%, transparent)" },
}

export function DashboardPage() {
  const [account, setAccount] = useState<Account | null>(null)
  const [posts, setPosts] = useState<Post[]>([])
  const [ready, setReady] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  const load = React.useCallback(async () => {
    setRefreshing(true)
    try {
      const [me, drafts] = await Promise.all([api("/api/v1/auth/me/"), api("/api/v1/drafts/?page_size=50")])
      const nextAccount = me.ok ? ((await me.json()) as { user: Account }).user : null
      const nextPosts = drafts.ok ? (((await drafts.json()) as Paginated<Post>).results ?? []) : []
      setAccount(nextAccount)
      setPosts(nextPosts)
      setReady(true)
    } catch {
      setReady(true)
    } finally {
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    let active = true
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load().then(() => {
      if (!active) return
    })
    return () => {
      active = false
    }
  }, [load])

  const name = account ? accountLabel(account) : "there"
  const inProgress = posts.filter((post) => post.status !== "published" && post.status !== "archived").length
  const published = posts.filter((post) => post.status === "published")
  const needsAttention = posts.filter((post) => post.status === "changes_requested" || post.status === "in_review").length
  const statusSlices = useMemo(() => countByStatus(posts), [posts])
  const [weekSeries, setWeekSeries] = useState<WeekPoint[]>([])
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setWeekSeries(lastEightWeeks(posts))
  }, [posts])

  const recent = useMemo(
    () => [...posts].sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()).slice(0, 6),
    [posts],
  )

  const [greeting, setGreeting] = useState("Hello")
  useEffect(() => {
    const hour = new Date().getHours()
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setGreeting(hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening")
  }, [])

  return (
    <AppShell eyebrow="Your desk" title={ready ? `${greeting}, ${name}.` : "Your desk"}>
      <div className="flex flex-wrap items-center gap-2">
        <Button asChild className="rounded-xl" size="lg">
          <Link href="/editor/new">
            <FilePenLine data-icon="inline-start" />
            New story
          </Link>
        </Button>
        <Button asChild variant="outline" className="rounded-xl" size="lg">
          <Link href="/compose">
            <Sparkles data-icon="inline-start" />
            Composer
          </Link>
        </Button>
        <Button asChild variant="outline" className="rounded-xl" size="lg">
          <Link href="/anna">
            <Bot data-icon="inline-start" />
            Ask Anna
          </Link>
        </Button>
        <button
          type="button"
          onClick={load}
          disabled={refreshing}
          className="ml-auto inline-flex items-center gap-1 rounded-lg border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:opacity-50"
        >
          <RefreshCw className={`size-3.5 ${refreshing ? "animate-spin" : ""}`} />
          Refresh
        </button>
        <Link href="/published" className="inline-flex items-center gap-1 text-sm text-primary interactive-link">
          Open published desk
          <ArrowUpRight className="size-4" />
        </Link>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Kpi label="Stories in progress" value={ready ? inProgress : "–"} icon={Layers3} tone="primary" hint="Drafts not yet published" />
        <Kpi label="Published" value={ready ? published.length : "–"} icon={Rocket} tone="success" hint="Live on Discover" />
        <Kpi
          label="Needs attention"
          value={ready ? needsAttention : "–"}
          icon={needsAttention > 0 ? AlertTriangle : CheckCircle2}
          tone={needsAttention > 0 ? "warning" : "muted"}
          hint="In review or changes requested"
        />
        <Kpi label="On this desk" value={ready ? posts.length : "–"} icon={Flame} tone="muted" hint="Total stories saved" />
      </div>

      <div className="mt-6 grid gap-5 xl:grid-cols-[20rem_1fr]">
        <section className="rounded-2xl border bg-card p-5">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-xl">Status mix</h2>
            <span className="text-xs text-muted-foreground">{posts.length} total</span>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">How your stories are split right now.</p>
          {ready && posts.length > 0 ? (
            <div key={JSON.stringify(statusSlices)} className="pie-enter">
              <StatusPie slices={statusSlices} />
            </div>
          ) : (
            <EmptyChart text={ready ? "Save a draft and the pie chart will fill in." : "Loading chart…"} />
          )}
        </section>
        <section className="rounded-2xl border bg-card p-5">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-xl">Writing activity</h2>
            <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
              <Clock3 className="size-3.5" />
              Last 8 weeks
            </span>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">Stories started in the last eight weeks.</p>
          {ready && posts.length > 0 ? (
            <ActivityGraph series={weekSeries} />
          ) : (
            <EmptyChart text={ready ? "Your graph appears after the first story is saved." : "Loading chart…"} />
          )}
        </section>
      </div>

      <section className="mt-8">
        <div className="flex items-end justify-between gap-4">
          <div>
            <h2 className="font-heading text-2xl">Recent stories</h2>
            <p className="mt-1 text-sm text-muted-foreground">Pick up where you left off.</p>
          </div>
          <Link className="interactive-link text-sm text-primary" href="/editor/new">
            New draft
          </Link>
        </div>
        {ready && posts.length === 0 ? (
          <div className="mt-4 flex flex-col items-start gap-3 rounded-2xl border bg-card px-6 py-10">
            <p className="text-sm leading-6 text-muted-foreground">
              No stories yet. Start your first draft and it will show up here.
            </p>
            <Button asChild className="rounded-xl">
              <Link href="/editor/new">
                <FilePenLine data-icon="inline-start" />
                Create first story
              </Link>
            </Button>
          </div>
        ) : (
          <div className="mt-4 grid gap-3">
            {recent.map((post) => {
              const style = STATUS_STYLE[post.status] ?? STATUS_STYLE.draft
              return (
                <Link
                  key={post.id}
                  href={post.status === "published" ? `/posts/${post.slug}` : `/editor/${post.id}`}
                  className="app-row group"
                >
                  <span className="min-w-0 flex-1">
                    <span className="flex items-center gap-2">
                      <span className="truncate font-medium">{post.title || "Untitled"}</span>
                      <span
                        className="shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide"
                        style={{ color: style.color, borderColor: style.ring, background: style.ring }}
                      >
                        {style.label}
                      </span>
                    </span>
                    <span className="mt-1 block truncate text-xs text-muted-foreground">
                      {post.category?.name ?? "No category"} · updated {formatDay(post.updated_at)}
                    </span>
                  </span>
                  <span className="inline-flex shrink-0 items-center gap-1 text-xs text-muted-foreground group-hover:text-foreground">
                    {post.status === "published" ? "Open live" : "Edit"}
                    <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-0.5" />
                  </span>
                </Link>
              )
            })}
          </div>
        )}
      </section>

      {ready && published.length > 0 ? (
        <section className="mt-10">
          <div className="flex items-end justify-between gap-4">
            <div>
              <h2 className="font-heading text-2xl">Published stories</h2>
              <p className="mt-1 text-sm text-muted-foreground">Live stories readers can open on Discover.</p>
            </div>
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            {published.slice(0, 4).map((post) => (
              <Link key={post.id} href={`/posts/${post.slug}`} className="story-card overflow-hidden rounded-2xl border bg-card">
                {post.featured_image ? (
                  <div className="relative aspect-[16/8] overflow-hidden bg-muted">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={mediaUrl(post.featured_image.url)} alt="" className="h-full w-full object-cover" />
                  </div>
                ) : (
                  <div className="aspect-[16/8] bg-muted" />
                )}
                <div className="p-5">
                  <p className="text-xs font-medium text-primary">{post.category?.name ?? "Uncategorized"}</p>
                  <h3 className="mt-2 font-heading text-xl">{post.title || "Untitled"}</h3>
                  <p className="mt-2 line-clamp-2 text-sm leading-6 text-muted-foreground">{post.excerpt}</p>
                  <p className="mt-3 text-xs text-muted-foreground">
                    {post.like_count ?? 0} likes · {post.comment_count ?? 0} comments
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </section>
      ) : null}
    </AppShell>
  )
}

function Kpi({
  label,
  value,
  icon: Icon,
  tone,
  hint,
}: {
  label: string
  value: string | number
  icon: React.ComponentType<{ className?: string }>
  tone: "primary" | "success" | "warning" | "muted"
  hint: string
}) {
  const toneClass =
    tone === "primary"
      ? "bg-primary/10 text-primary"
      : tone === "success"
        ? "bg-success/15 text-success"
        : tone === "warning"
          ? "bg-[color-mix(in_oklch,oklch(0.72_0.14_55)_15%,transparent)] text-[oklch(0.55_0.12_55)]"
          : "bg-muted text-muted-foreground"

  return (
    <div className="group rounded-2xl border bg-card p-5 shadow-sm transition-shadow hover:shadow-md">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium tracking-[0.14em] text-muted-foreground uppercase">{label}</p>
        <span className={`flex size-8 items-center justify-center rounded-lg ${toneClass}`}>
          <Icon className="size-4" />
        </span>
      </div>
      <p className="mt-3 font-heading text-4xl tracking-tight">{value}</p>
      <p className="mt-1 text-xs text-muted-foreground">{hint}</p>
    </div>
  )
}

function AlertTriangle({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  )
}

function EmptyChart({ text }: { text: string }) {
  return <p className="mt-8 text-sm text-muted-foreground">{text}</p>
}

function StatusPie({ slices }: { slices: Slice[] }) {
  const total = slices.reduce((sum, slice) => sum + slice.value, 0)
  const gradient = conicGradient(slices, total)

  return (
    <div className="mt-6 flex flex-col items-center gap-6 sm:flex-row sm:items-center">
      <div className="relative size-40 shrink-0">
        <div
          className="size-full rounded-full"
          style={{ background: gradient }}
          role="img"
          aria-label={slices.map((slice) => `${slice.label} ${slice.value}`).join(", ")}
        />
        <div className="absolute inset-[1.5rem] flex flex-col items-center justify-center rounded-full bg-card">
          <p className="font-heading text-3xl">{total}</p>
          <p className="text-[11px] text-muted-foreground">stories</p>
        </div>
      </div>
      <ul className="w-full space-y-2 text-sm">
        {slices.map((slice) => (
          <li key={slice.status} className="flex items-center justify-between gap-3">
            <span className="inline-flex min-w-0 items-center gap-2">
              <span className="size-2.5 shrink-0 rounded-full" style={{ background: slice.color }} />
              <span className="truncate">{slice.label}</span>
            </span>
            <span className="shrink-0 text-muted-foreground">
              {slice.value} · {Math.round((slice.value / total) * 100)}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function ActivityGraph({ series }: { series: WeekPoint[] }) {
  const max = Math.max(...series.map((point) => point.value), 1)
  const width = 560
  const height = 180
  const padX = 18
  const padY = 16
  const innerW = width - padX * 2
  const innerH = height - padY * 2 - 18
  const step = series.length > 1 ? innerW / (series.length - 1) : innerW
  const points = series.map((point, index) => {
    const x = padX + index * step
    const y = padY + innerH - (point.value / max) * innerH
    return `${x},${y}`
  })
  const area = `${padX},${padY + innerH} ${points.join(" ")} ${padX + (series.length - 1) * step},${padY + innerH}`

  return (
    <div className="mt-5">
      <svg viewBox={`0 0 ${width} ${height}`} className="h-48 w-full" role="img" aria-label="Stories started over the last eight weeks">
        <defs>
          <linearGradient id="desk-area" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="var(--primary)" stopOpacity="0.28" />
            <stop offset="100%" stopColor="var(--primary)" stopOpacity="0.02" />
          </linearGradient>
        </defs>
        {[0.25, 0.5, 0.75, 1].map((line) => (
          <line
            key={line}
            x1={padX}
            x2={width - padX}
            y1={padY + innerH * (1 - line)}
            y2={padY + innerH * (1 - line)}
            stroke="var(--border)"
            strokeDasharray="4 6"
          />
        ))}
        <polygon points={area} fill="url(#desk-area)" />
        <polyline points={points.join(" ")} fill="none" stroke="var(--primary)" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round" />
        {series.map((point, index) => {
          const x = padX + index * step
          const y = padY + innerH - (point.value / max) * innerH
          return (
            <g key={point.label}>
              <circle cx={x} cy={y} r="4.5" fill="var(--card)" stroke="var(--primary)" strokeWidth="2" />
              <text x={x} y={height - 2} textAnchor="middle" className="fill-muted-foreground" fontSize="11">
                {point.label}
              </text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}

type Slice = { status: string; label: string; value: number; color: string }
export type WeekPoint = { label: string; value: number }

function countByStatus(posts: Post[]): Slice[] {
  const counts = new Map<string, number>()
  for (const status of Object.keys(STATUS_STYLE)) counts.set(status, 0)
  for (const post of posts) counts.set(post.status, (counts.get(post.status) ?? 0) + 1)
  return [...counts.entries()]
    .filter(([, value]) => value > 0)
    .map(([status, value]) => ({
      status,
      value,
      label: labelFor(status),
      color: STATUS_STYLE[status]?.color ?? "var(--muted-foreground)",
    }))
}

function lastEightWeeks(posts: Post[]): WeekPoint[] {
  const now = new Date()
  const start = startOfWeek(addDays(now, -7 * 7))
  return Array.from({ length: 8 }, (_, index) => {
    const weekStart = addDays(start, index * 7)
    const weekEnd = addDays(weekStart, 7)
    const value = posts.filter((post) => {
      const created = new Date(post.created_at)
      return created >= weekStart && created < weekEnd
    }).length
    return { label: weekStart.toLocaleDateString(undefined, { month: "short", day: "numeric" }), value }
  })
}

function conicGradient(slices: Slice[], total: number) {
  let cursor = 0
  const stops = slices.map((slice) => {
    const start = cursor
    cursor += (slice.value / total) * 100
    return `${slice.color} ${start}% ${cursor}%`
  })
  return `conic-gradient(${stops.join(", ")})`
}

function labelFor(status: string) {
  return STATUS_STYLE[status]?.label ?? status.replaceAll("_", " ")
}

function formatDay(value: string) {
  return new Date(value).toLocaleDateString()
}

function startOfWeek(date: Date) {
  const next = new Date(date)
  const day = next.getDay()
  next.setHours(0, 0, 0, 0)
  next.setDate(next.getDate() - day)
  return next
}

function addDays(date: Date, days: number) {
  const next = new Date(date)
  next.setDate(next.getDate() + days)
  return next
}
