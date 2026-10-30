"use client"

import { useEffect, useState, useSyncExternalStore } from "react"

type CyclingTextProps = {
  phrases: readonly string[]
  typingMs?: number
  pauseMs?: number
  variant?: "inline" | "overlay"
  className?: string
}

/** A decorative prompt preview. The actual input remains empty and editable. */
export function CyclingText({
  phrases,
  typingMs = 38,
  pauseMs = 1300,
  variant = "overlay",
  className,
}: CyclingTextProps) {
  const [phraseIndex, setPhraseIndex] = useState(0)
  const [count, setCount] = useState(0)
  const [deleting, setDeleting] = useState(false)
  const reducedMotion = useSyncExternalStore(
    (notify) => {
      const media = window.matchMedia("(prefers-reduced-motion: reduce)")
      media.addEventListener("change", notify)
      return () => media.removeEventListener("change", notify)
    },
    () => window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    () => false,
  )

  useEffect(() => {
    if (reducedMotion || phrases.length === 0) return

    const phrase = phrases[phraseIndex] ?? ""
    const complete = count === phrase.length
    const empty = count === 0
    const delay = !deleting && complete ? pauseMs : deleting ? typingMs / 2 : typingMs

    const timer = window.setTimeout(() => {
      if (!deleting && complete) {
        setDeleting(true)
      } else if (deleting && empty) {
        setDeleting(false)
        setPhraseIndex((current) => (current + 1) % phrases.length)
      } else {
        setCount((current) => current + (deleting ? -1 : 1))
      }
    }, delay)

    return () => window.clearTimeout(timer)
  }, [count, deleting, pauseMs, phraseIndex, phrases, reducedMotion, typingMs])

  const phrase = phrases[phraseIndex] ?? ""
  const visibleCount = reducedMotion ? phrase.length : count

  return (
    <span
      aria-hidden="true"
      className={
        variant === "overlay"
          ? `pointer-events-none absolute inset-y-0 left-2.5 flex items-center text-xs text-muted-foreground ${className ?? ""}`
          : `inline-flex items-baseline ${className ?? ""}`
      }
    >
      {phrase.slice(0, visibleCount)}
      {!reducedMotion ? <span className="caret ml-px">|</span> : null}
    </span>
  )
}
