"use client"

import { useEffect, useRef } from "react"
import { cn } from "cn"

export function Reveal({
  children,
  className,
  delay = 0,
}: {
  children: React.ReactNode
  className?: string
  delay?: number
}) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const node = ref.current
    if (!node) return
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return

    const visible = () => {
      const rect = node.getBoundingClientRect()
      return rect.top < window.innerHeight * 0.92 && rect.bottom > 0
    }

    if (visible()) return

    node.classList.add("reveal-armed")
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry?.isIntersecting) return
        node.setAttribute("data-visible", "")
        observer.disconnect()
      },
      { threshold: 0.08 }
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [])

  return (
    <div ref={ref} className={cn("reveal", className)} style={{ transitionDelay: `${delay}ms` }}>
      {children}
    </div>
  )
}
