"use client"

import { useState } from "react"
import Image from "next/image"
import { Check, Feather, FileText, ListChecks, PenLine, Search, Sparkles } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "cn"
import { draftSeed, previewPanels, type PreviewPanelId } from "@/features/public-blog/content"

const rail = [
  { id: "write" as const, label: "Write", icon: PenLine },
  { id: "research" as const, label: "Research", icon: Search },
  { id: "anna" as const, label: "Anna", icon: Sparkles },
  { id: "sources" as const, label: "Sources", icon: FileText },
  { id: "review" as const, label: "Review", icon: ListChecks },
]

const workspacePanels: Record<
  PreviewPanelId,
  { eyebrow: string; title: string; body: string; items: string[] }
> = {
  write: {
    eyebrow: "Draft workspace",
    title: "A focused page, not a noisy canvas.",
    body: "Keep the article and its decisions in one calm place.",
    items: ["Featured image attached", "Draft saved locally", "Category ready to choose"],
  },
  research: {
    eyebrow: "Research brief",
    title: "Start with the question behind the story.",
    body: "Anna keeps the scope visible before a draft begins.",
    items: ["Audience: informed readers", "Angle: practical change", "Length: 900–1,200 words"],
  },
  anna: {
    eyebrow: "Anna suggestion",
    title: "A stronger opening begins with one concrete scene.",
    body: "Suggested, not inserted. The author decides what belongs in the final piece.",
    items: ["Title directions", "Outline options", "Revision notes"],
  },
  sources: {
    eyebrow: "Source desk",
    title: "Three sources are ready for review.",
    body: "Each keeps a clear title, publisher, and retrieval time before it supports a claim.",
    items: ["IEA · retrieved today", "Nature · retrieved today", "Reuters · retrieved yesterday"],
  },
  review: {
    eyebrow: "Human review",
    title: "Nothing publishes without an author action.",
    body: "The final pass keeps ownership, sources, and status visible.",
    items: ["Content reviewed", "Sources attached", "Ready for author approval"],
  },
}

export function ProductStage() {
  const [panel, setPanel] = useState<PreviewPanelId>("write")
  const active = workspacePanels[panel]

  return (
    <div className="relative min-w-0">
      <div
        aria-hidden="true"
        className="atmosphere-blob pointer-events-none absolute -top-10 -right-8 -z-10 size-56 rounded-full bg-primary/15 blur-3xl"
      />
      <div className="overflow-hidden rounded-2xl bg-card text-card-foreground shadow-xl ring-1 ring-foreground/10">
        <div className="flex items-center gap-2 border-b px-3 py-2">
          <span className="inline-flex items-center gap-1.5 text-xs font-medium">
            <Feather aria-hidden="true" className="size-3.5 text-primary" />
            SwiftPost
          </span>
          <span className="hidden min-w-0 truncate text-xs text-muted-foreground sm:inline">
            {draftSeed.kicker}
          </span>
          <Badge variant="outline" className="ml-auto text-[10px]">Author workspace</Badge>
        </div>

        <div className="flex gap-1 overflow-x-auto border-b p-2 lg:hidden">
          {previewPanels.map((item) => (
            <Button
              key={item.id}
              type="button"
              size="sm"
              variant={panel === item.id ? "secondary" : "ghost"}
              aria-pressed={panel === item.id}
              onClick={() => setPanel(item.id)}
            >
              {item.label}
            </Button>
          ))}
        </div>

        <div className="grid lg:grid-cols-[3.25rem_minmax(0,1.1fr)_minmax(15rem,0.9fr)]">
          <nav aria-label="Workspace preview" className="hidden flex-col gap-1 border-r p-2 lg:flex">
            {rail.map((item) => {
              const Icon = item.icon
              return (
                <Button
                  key={item.id}
                  type="button"
                  size="icon"
                  variant={panel === item.id ? "secondary" : "ghost"}
                  aria-pressed={panel === item.id}
                  aria-label={item.label}
                  onClick={() => setPanel(item.id)}
                >
                  <Icon />
                </Button>
              )
            })}
          </nav>

          <section className={cn("min-w-0 border-b lg:border-r lg:border-b-0", panel === "write" ? "block" : "hidden lg:block")}>
            <div className="flex h-[22rem] flex-col gap-3 p-4 lg:h-[26rem]">
              <div aria-hidden="true" className="flex gap-2 text-[11px] text-muted-foreground">
                <span className="rounded-md bg-muted px-1.5 py-0.5">Paragraph</span><span>Bold</span><span>List</span>
              </div>
              <h2 className="font-heading text-2xl leading-tight tracking-tight">{draftSeed.title}</h2>
              <div className="relative aspect-[16/9] overflow-hidden rounded-lg">
                <Image src="/landing/turbines.jpg" alt="Wind turbines in a field at sunset" fill sizes="(min-width: 1024px) 28rem, 100vw" className="object-cover" priority />
              </div>
              <p className="text-sm leading-6 text-muted-foreground">{draftSeed.lede}</p>
              <Badge variant="outline" className="w-fit">Draft · not published</Badge>
            </div>
          </section>

          <section className="min-w-0 bg-muted/35" aria-live="polite">
            <div className="flex h-[22rem] flex-col p-4 lg:h-[26rem]">
              <p className="text-[11px] font-medium tracking-[0.16em] text-primary uppercase">{active.eyebrow}</p>
              <h2 className="mt-3 font-heading text-2xl leading-tight tracking-tight">{active.title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{active.body}</p>
              <ul className="mt-auto flex flex-col gap-2 border-t pt-4">
                {active.items.map((item) => (
                  <li key={item} className="flex items-center gap-2 text-xs">
                    <Check className="size-3.5 text-primary" aria-hidden="true" />
                    {item}
                  </li>
                ))}
              </ul>
              <p className="mt-4 text-[11px] leading-5 text-muted-foreground">
                Research, drafting, and approval stay connected without bypassing the author.
              </p>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
