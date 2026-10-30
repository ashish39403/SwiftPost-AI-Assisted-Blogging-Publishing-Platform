"use client"

import { useEffect } from "react"

/** Keep a direct reload of the public landing route anchored at its opening. */
export function LandingScrollReset() {
  useEffect(() => {
    const previousRestoration = window.history.scrollRestoration
    window.history.scrollRestoration = "manual"
    const frame = window.requestAnimationFrame(() => window.scrollTo({ top: 0, left: 0, behavior: "auto" }))

    return () => {
      window.cancelAnimationFrame(frame)
      window.history.scrollRestoration = previousRestoration
    }
  }, [])

  return null
}
