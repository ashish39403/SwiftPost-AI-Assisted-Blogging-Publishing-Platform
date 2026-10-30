"use client"

import { useEffect, useState } from "react"

export function TypedText({ text, ms = 16 }: { text: string; ms?: number }) {
  const [count, setCount] = useState(0)

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      const id = window.setTimeout(() => setCount(text.length), 0)
      return () => window.clearTimeout(id)
    }
    if (count >= text.length) return
    const id = window.setTimeout(() => setCount((value) => value + 1), ms)
    return () => window.clearTimeout(id)
  }, [count, ms, text.length])

  const typing = count < text.length

  return (
    <span>
      {text.slice(0, count)}
      {typing ? (
        <span className="caret" aria-hidden="true">
          |
        </span>
      ) : null}
    </span>
  )
}
