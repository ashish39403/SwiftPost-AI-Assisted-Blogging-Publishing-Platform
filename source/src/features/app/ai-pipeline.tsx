"use client"

import { useEffect, useState } from "react"

export const COMPOSE_PIPELINE = [
  "Reading the title",
  "Searching live images",
  "Writing the article",
  "Saving a private draft",
]

export const ANNA_PIPELINE = [
  "Opening the draft",
  "Checking the structure",
  "Writing review notes",
]

export function AiPipeline({ steps }: { steps: readonly string[] }) {
  const [step, setStep] = useState(0)

  useEffect(() => {
    const id = window.setInterval(() => {
      setStep((current) => Math.min(current + 1, steps.length - 1))
    }, 1600)
    return () => window.clearInterval(id)
  }, [steps])

  return (
    <ol className="ai-pipeline" aria-live="polite" aria-label="Generation progress">
      {steps.map((label, index) => {
        const state = index < step ? "done" : index === step ? "active" : "wait"
        return (
          <li key={label} data-state={state}>
            <span className="pipe-dot" />
            <span>
              <span className="block text-[11px] font-medium tracking-[.14em] text-muted-foreground uppercase">
                {state === "done" ? "Done" : state === "active" ? "Working" : "Waiting"}
              </span>
              {label}
            </span>
          </li>
        )
      })}
    </ol>
  )
}
