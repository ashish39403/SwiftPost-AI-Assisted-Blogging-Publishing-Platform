"use client"

import Link from "next/link"
import type { MouseEvent } from "react"
import { HeaderAccount } from "@/features/public-blog/header-account"
import { Logo } from "@/features/public-blog/logo"

const links = [
  { href: "/discover", label: "Discover" },
  { href: "/#authors", label: "For Authors" },
  { href: "/#how-it-works", label: "How It Works" },
]

export function SiteHeader() {
  function returnToLandingTop(event: MouseEvent<HTMLAnchorElement>) {
    if (window.location.pathname !== "/") return

    event.preventDefault()
    window.history.replaceState(null, "", "/")
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches
    window.scrollTo({ top: 0, left: 0, behavior: reducedMotion ? "auto" : "smooth" })
  }

  return (
    <header className="site-header sticky top-0 z-40 border-b bg-background/85 backdrop-blur-md">
      <a
        href="#content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded-md focus:bg-background focus:px-3 focus:py-2 focus:ring-3 focus:ring-ring/50"
      >
        Skip to content
      </a>
      <div className="mx-auto flex w-full max-w-7xl items-center gap-3 px-5 py-3 md:px-8">
        <Link href="/" className="brand-link text-foreground" aria-label="SwiftPost home" onClick={returnToLandingTop}>
          <Logo />
        </Link>
        <nav aria-label="Primary" className="absolute left-1/2 hidden -translate-x-1/2 items-center gap-6 md:flex">
          {links.map((link) => (
              <Link
              key={link.href}
              href={link.href}
              className="interactive-link text-sm text-muted-foreground"
            >
              {link.label}
              </Link>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <HeaderAccount />
        </div>
      </div>
      <nav
        aria-label="On this page"
        className="mx-auto flex w-full max-w-7xl gap-4 overflow-x-auto px-5 pb-3 md:hidden"
      >
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="interactive-link shrink-0 text-sm text-muted-foreground"
          >
            {link.label}
          </Link>
        ))}
      </nav>
    </header>
  )
}
