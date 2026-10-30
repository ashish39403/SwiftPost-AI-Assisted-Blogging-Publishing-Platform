"use client"

import { Suspense, useEffect, useRef, useState } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import {
  Bot,
  FilePenLine,
  LayoutDashboard,
  Menu,
  Newspaper,
  Plus,
  Settings,
  Search,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { AccountMenu } from "@/features/auth/account-menu"
import { Logo } from "@/features/public-blog/logo"
import { api, type Account } from "@/lib/api"

const links = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/stories", label: "Stories", icon: FilePenLine },
  { href: "/compose", label: "Composer", icon: Sparkles },
  { href: "/published", label: "Published", icon: Newspaper },
  { href: "/anna", label: "Anna", icon: Bot },
  { href: "/admin", label: "Admin", icon: ShieldCheck },
  { href: "/settings", label: "Settings", icon: Settings },
]

function navActive(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`) || (href === "/stories" && pathname.startsWith("/editor"))
}

function WorkspaceNav({
  visibleLinks,
  onNavigate,
}: {
  visibleLinks: typeof links
  onNavigate?: () => void
}) {
  const pathname = usePathname()
  return (
    <nav className="mt-4 flex flex-col gap-1 px-3" aria-label="Author workspace">
      {visibleLinks.map(({ href, label, icon: Icon }) => {
        const active = navActive(pathname, href)
        return (
          <Link
            key={href}
            href={href}
            onClick={onNavigate}
            className={`app-nav-link ${active ? "app-nav-link-active" : ""}`}
            aria-current={active ? "page" : undefined}
          >
            <Icon className="size-4" />
            {label}
          </Link>
        )
      })}
    </nav>
  )
}

export function AppShell({ title, eyebrow, children, wide = false }: { title: string; eyebrow: string; children: React.ReactNode; wide?: boolean }) {
  const router = useRouter()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [mobileClosing, setMobileClosing] = useState(false)
  const mobileCloseTimer = useRef<number | null>(null)
  const [account, setAccount] = useState<Account | null>(null)
  const [workspaceSearch, setWorkspaceSearch] = useState("")

  useEffect(() => {
    api("/api/v1/auth/me/")
      .then(async (response) => setAccount(response.ok ? ((await response.json()) as { user: Account }).user : null))
      .catch(() => setAccount(null))
  }, [])
  const visibleLinks = links.filter((link) => link.href !== "/admin" || account?.role === "admin")

  function openMobileNav() {
    if (mobileCloseTimer.current !== null) window.clearTimeout(mobileCloseTimer.current)
    setMobileClosing(false)
    setMobileOpen(true)
  }

  function closeMobileNav() {
    setMobileClosing(true)
    mobileCloseTimer.current = window.setTimeout(() => {
      setMobileOpen(false)
      setMobileClosing(false)
      mobileCloseTimer.current = null
    }, 280)
  }

  useEffect(() => () => {
    if (mobileCloseTimer.current !== null) window.clearTimeout(mobileCloseTimer.current)
  }, [])

  function submitWorkspaceSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const query = workspaceSearch.trim()
    router.push(query ? `/stories?search=${encodeURIComponent(query)}` : "/stories")
  }

  return (
    <main className="app-canvas flex min-h-dvh w-full">
      <aside className="app-sidebar hidden w-64 shrink-0 flex-col border-r border-border bg-card/60 backdrop-blur lg:flex">
        <div className="flex items-center gap-2 px-5 py-5">
          <Link href="/" className="brand-link inline-flex items-center gap-2 text-foreground" aria-label="SwiftPost home">
            <Logo />
          </Link>
        </div>
        <div className="px-3">
          <Button asChild className="w-full justify-start rounded-xl" size="lg">
            <Link href="/editor/new">
              <Plus data-icon="inline-start" />
              New story
            </Link>
          </Button>
        </div>
        <Suspense fallback={<nav className="mt-4 flex flex-col gap-1 px-3" aria-label="Author workspace" />}>
          <WorkspaceNav visibleLinks={visibleLinks} />
        </Suspense>
        <div className="mt-auto px-3 pb-4">
          <div className="rounded-xl border border-border bg-muted/40 p-3">
            <p className="text-xs font-medium">Your desk</p>
            <p className="mt-1 text-[11px] leading-5 text-muted-foreground">
              Stories shown here come from your account.
            </p>
          </div>
        </div>
      </aside>

      {mobileOpen ? (
        <div className={`mobile-nav fixed inset-0 z-50 lg:hidden ${mobileClosing ? "mobile-nav-closing" : "mobile-nav-open"}`}>
          <button
            type="button"
            aria-label="Close menu"
            className="mobile-nav-backdrop absolute inset-0 bg-foreground/40 backdrop-blur-sm"
            onClick={closeMobileNav}
          />
          <aside className="mobile-nav-drawer relative flex h-dvh w-72 max-w-[85vw] flex-col border-r border-border bg-card shadow-xl">
            <div className="flex items-center justify-between px-5 py-4">
              <Link href="/" className="brand-link inline-flex items-center gap-2 text-foreground" onClick={closeMobileNav}>
                <Logo />
              </Link>
              <button
                type="button"
                aria-label="Close menu"
                className="app-icon-button"
                onClick={closeMobileNav}
              >
                <X className="size-4" />
              </button>
            </div>
            <div className="px-3">
              <Button asChild className="w-full justify-start rounded-xl" size="lg" onClick={closeMobileNav}>
                <Link href="/editor/new">
                  <Plus data-icon="inline-start" />
                  New story
                </Link>
              </Button>
            </div>
            <Suspense fallback={<nav className="mt-4 flex flex-col gap-1 px-3" aria-label="Author workspace" />}>
              <WorkspaceNav visibleLinks={visibleLinks} onNavigate={closeMobileNav} />
            </Suspense>
          </aside>
        </div>
      ) : null}

      <section className="app-content flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="app-toolbar sticky top-0 z-30 flex items-center gap-3 border-b border-border bg-background/80 px-4 py-3 backdrop-blur md:px-6">
          <button
            type="button"
            aria-label="Open menu"
            className="app-icon-button lg:hidden"
            onClick={openMobileNav}
          >
            <Menu className="size-4" />
          </button>
          <form className="relative hidden max-w-md flex-1 md:block" onSubmit={submitWorkspaceSearch}>
            <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
            <input
              aria-label="Search workspace"
              placeholder="Search your stories"
              className="app-search w-full"
              value={workspaceSearch}
              onChange={(event) => setWorkspaceSearch(event.target.value)}
            />
          </form>
          <div className="ml-auto flex items-center gap-2">
            <AccountMenu />
          </div>
        </header>

        <div className="flex-1 overflow-y-auto">
          <div className={`mx-auto w-full px-4 py-6 md:px-8 md:py-8 ${wide ? "max-w-[110rem]" : "max-w-7xl"}`}>
            <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className="text-[11px] font-medium tracking-[0.18em] text-primary uppercase">
                  {eyebrow}
                </p>
                <h1 className="mt-2 font-heading text-2xl tracking-tight md:text-4xl">
                  {title}
                </h1>
              </div>
            </div>
            {children}
          </div>
        </div>
      </section>
    </main>
  )
}
