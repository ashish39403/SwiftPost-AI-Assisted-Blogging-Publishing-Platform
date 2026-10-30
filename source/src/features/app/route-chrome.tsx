"use client"

import { Suspense, useEffect, useState } from "react"
import { usePathname, useRouter } from "next/navigation"
import { SiteFooter } from "@/features/public-blog/site-footer"
import { SiteHeader } from "@/features/public-blog/site-header"
import { api, type Account } from "@/lib/api"

const workspacePrefixes = ["/dashboard", "/editor", "/stories", "/compose", "/published", "/anna", "/admin", "/settings"]

function isWorkspacePath(pathname: string) {
  return workspacePrefixes.some((prefix) => pathname.startsWith(prefix))
}

export function RouteChrome({ children }: { children: React.ReactNode }) {
  return (
    <div id="top" className="flex min-h-dvh flex-col">
      <Suspense fallback={null}>
        <PublicHeader />
      </Suspense>
      {children}
      <Suspense fallback={null}>
        <AfterPageChrome />
      </Suspense>
    </div>
  )
}

function PublicHeader() {
  const pathname = usePathname()
  if (isWorkspacePath(pathname)) return null
  return <SiteHeader />
}

function AfterPageChrome() {
  const pathname = usePathname()
  if (isWorkspacePath(pathname)) return <WorkspaceGate />
  return <SiteFooter />
}

function WorkspaceGate() {
  const pathname = usePathname()
  const router = useRouter()
  const [account, setAccount] = useState<Account | null | undefined>(undefined)

  useEffect(() => {
    api("/api/v1/auth/me/")
      .then(async (response) => {
        if (!response.ok) {
          setAccount(null)
          return
        }
        setAccount(((await response.json()) as { user: Account }).user)
      })
      .catch(() => setAccount(null))
  }, [])

  useEffect(() => {
    if (account === undefined) return
    if (!account) {
      router.replace("/login")
      return
    }
    if (account.role === "reader") {
      router.replace("/discover")
      return
    }
    if (pathname.startsWith("/admin") && account.role !== "admin") {
      router.replace("/dashboard")
    }
  }, [account, pathname, router])

  const allowed = Boolean(
    account && account.role !== "reader" && (!pathname.startsWith("/admin") || account.role === "admin"),
  )

  if (allowed) return null

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-background text-sm text-muted-foreground">
      Opening your workspace…
    </div>
  )
}
