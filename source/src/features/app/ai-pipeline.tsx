"use client"

import { useEffect, useState } from "react"

export const COMPOSE_PIPELINE = [
  { label: "Reading the brief", holdMs: 4000 },
  { label: "Writing the article", holdMs: 240000 },
  { label: "Finding live images", holdMs: 40000 },
  { label: "Saving a private draft", holdMs: 20000 },
] as const

export const ANNA_PIPELINE = [
  { label: "Opening the draft", holdMs: 2500 },
  { label: "Checking the structure", holdMs: 8000 },
  { label: "Writing review notes", holdMs: 180000 },
] as const

type PipelineStep = { readonly label: string; readonly holdMs: number }

export function AiPipeline({ steps }: { steps: readonly PipelineStep[] }) {
  const [step, setStep] = useState(0)

  useEffect(() => {
    const timers: number[] = []
    let elapsed = 0
    steps.forEach((item, index) => {
      if (index === 0) return
      elapsed += steps[index - 1].holdMs
      timers.push(window.setTimeout(() => setStep(index), elapsed))
    })
    return () => timers.forEach((id) => window.clearTimeout(id))
  }, [steps])

  return (
    <ol className="ai-pipeline" aria-live="polite" aria-label="Generation progress">
      {steps.map((item, index) => {
        const state = index < step ? "done" : index === step ? "active" : "wait"
        return (
          <li key={item.label} data-state={state}>
            <span className="pipe-dot" />
            <span>
              <span className="block text-[11px] font-medium tracking-[.14em] text-muted-foreground uppercase">
                {state === "done" ? "Done" : state === "active" ? "Working" : "Waiting"}
              </span>
              {item.label}
            </span>
          </li>
        )
      })}
    </ol>
  )
}
