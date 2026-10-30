import { ArrowRight, Check, FileText, Search, Sparkles, Upload } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "cn"
import { capabilities, heroStoryWords, steps } from "@/features/public-blog/content"
import { CyclingText } from "@/features/public-blog/cycling-text"
import { LiveStoriesSection } from "@/features/public-blog/live-stories-section"
import { ProductStage } from "@/features/public-blog/product-stage"
import { Reveal } from "@/features/public-blog/reveal"

const capabilityIcons = {
  research: Search,
  writing: FileText,
  publish: Upload,
} as const

export function LandingPage() {
  return (
    <>
      <section className="relative overflow-x-clip">
        <div aria-hidden="true" className="atmosphere-blob pointer-events-none absolute -top-24 right-[8%] size-[28rem] rounded-full bg-primary/12 blur-3xl" />
        <div aria-hidden="true" className="atmosphere-blob pointer-events-none absolute top-40 -left-24 size-64 rounded-full bg-highlight/20 blur-3xl" />
        <div className="mx-auto grid w-full max-w-7xl items-center gap-10 px-5 py-12 md:px-8 md:py-16 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:py-20">
          <div className="hero-enter flex max-w-xl flex-col gap-6">
            <p className="text-[11px] font-medium tracking-[0.22em] text-muted-foreground uppercase">
              A smarter way to blog and publish
            </p>
            <h1 className="font-heading text-[clamp(2.6rem,5.6vw,4.75rem)] leading-[0.98] tracking-[-0.035em] text-foreground">
              <span className="sr-only">Turn ideas into stories worth reading.</span>
              <span aria-hidden="true">
                Turn ideas into{" "}
                <span className="relative inline-block text-primary">
                  <CyclingText phrases={heroStoryWords} typingMs={72} pauseMs={1450} variant="inline" />
                <svg
                  viewBox="0 0 200 16"
                  aria-hidden="true"
                  className="scribble absolute -bottom-1 left-0 h-3.5 w-full text-highlight"
                >
                  <path
                    d="M4 10 C 40 3, 96 15, 196 6"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="3.5"
                    strokeLinecap="round"
                  />
                </svg>
                </span>{" "}
                worth reading.
              </span>
            </h1>
            <p className="max-w-md text-lg leading-8 text-muted-foreground">
              Research smarter. Write better. Publish with confidence.
            </p>
            <div className="flex flex-wrap gap-3">
              <Button asChild className="h-11 rounded-full px-5">
                <a href="/signup">
                  Start writing
                  <ArrowRight data-icon="inline-end" />
                </a>
              </Button>
              <Button variant="outline" asChild className="h-11 rounded-full px-5">
                <a href="/discover">
                  <Sparkles data-icon="inline-start" />
                  Explore stories
                </a>
              </Button>
            </div>
            <ul className="flex flex-col gap-2 text-sm sm:flex-row sm:flex-wrap sm:gap-x-5">
              {[
                "AI-assisted writing",
                "Author-controlled publishing",
                "Built for real readers",
              ].map((item) => (
                <li key={item} className="inline-flex items-center gap-2">
                  <Check aria-hidden="true" className="size-4 text-primary" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
          <ProductStage />
        </div>
      </section>

      <LiveStoriesSection />

      <section id="capabilities" className="scroll-mt-24 border-t">
        <div className="mx-auto grid w-full max-w-7xl gap-8 px-5 py-14 md:grid-cols-3 md:px-8 md:py-16">
          {capabilities.map((item, index) => {
            const Icon = capabilityIcons[item.tone]
            const surface =
              item.tone === "research"
                ? "bg-feature-research text-primary"
                : item.tone === "writing"
                  ? "bg-feature-writing text-primary"
                  : "bg-feature-publish text-highlight"
            return (
              <Reveal key={item.title} delay={index * 50}>
                <div className="flex gap-4">
                  <span
                    className={cn(
                      "flex size-12 shrink-0 items-center justify-center rounded-full",
                      surface
                    )}
                  >
                    <Icon aria-hidden="true" className="size-5" />
                  </span>
                  <div className="flex flex-col gap-1.5">
                    <h2 className="font-heading text-xl tracking-tight">{item.title}</h2>
                    <p className="text-sm leading-6 text-muted-foreground">{item.body}</p>
                  </div>
                </div>
              </Reveal>
            )
          })}
        </div>
      </section>

      <section id="how-it-works" className="scroll-mt-24 border-t bg-muted/50">
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-5 py-16 md:px-8 md:py-20">
          <Reveal>
            <div className="max-w-2xl">
              <p className="text-[11px] font-medium tracking-[0.18em] text-primary uppercase">
                How it works
              </p>
              <h2 className="mt-3 font-heading text-4xl leading-tight tracking-tight">
                Research. Shape. Publish — with the author still in charge.
              </h2>
            </div>
          </Reveal>
          <div className="grid gap-4 md:grid-cols-3">
            {steps.map((step, index) => (
              <Reveal key={step.number} delay={index * 50}>
                <article className="workflow-card flex h-full flex-col gap-3 rounded-xl bg-card p-5">
                  <span className="text-xs font-medium text-primary">{step.number}</span>
                  <h3 className="font-heading text-2xl tracking-tight">{step.title}</h3>
                  <p className="text-sm leading-6 text-muted-foreground">{step.body}</p>
                </article>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section id="authors" className="scroll-mt-24">
        <div className="mx-auto grid w-full max-w-7xl gap-8 px-5 py-16 md:grid-cols-2 md:px-8 md:py-20">
          <Reveal>
            <div className="flex flex-col gap-3">
              <p className="text-[11px] font-medium tracking-[0.18em] text-primary uppercase">
                For authors
              </p>
              <h2 className="font-heading text-4xl leading-tight tracking-tight">
                A desk for the piece you are willing to sign.
              </h2>
              <p className="max-w-md text-sm leading-6 text-muted-foreground">
                Sign-in will open your own drafts. Anna can research and revise beside the editor. Nothing she writes becomes public until you confirm it.
              </p>
            </div>
          </Reveal>
          <Reveal delay={60}>
            <ul className="flex flex-col gap-4">
              {[
                ["Your posts", "Drafts and published stories stay tied to your account."],
                ["Visible sources", "A researched claim keeps its link and retrieval time."],
                ["A human gate", "Save or publish are actions you take, not side effects of a chat reply."],
              ].map(([title, body]) => (
                <li key={title} className="flex flex-col gap-1 border-b pb-4">
                  <h3 className="font-medium">{title}</h3>
                  <p className="text-sm leading-6 text-muted-foreground">{body}</p>
                </li>
              ))}
            </ul>
          </Reveal>
        </div>
      </section>

      <section className="relative overflow-hidden border-t">
        <div aria-hidden="true" className="cta-wave pointer-events-none absolute inset-x-0 bottom-0 h-40" />
        <div className="relative mx-auto flex w-full max-w-3xl flex-col items-center gap-5 px-5 py-20 text-center">
          <h2 className="font-heading text-4xl tracking-tight">
            A more inspired internet starts with you.
          </h2>
          <p className="max-w-md text-sm leading-6 text-muted-foreground">
            Join a growing desk for writers who want research close at hand and the byline still theirs.
          </p>
          <Button asChild className="h-11 rounded-full px-6">
            <a href="/signup">
              Start writing
              <ArrowRight data-icon="inline-end" />
            </a>
          </Button>
        </div>
      </section>
    </>
  )
}
