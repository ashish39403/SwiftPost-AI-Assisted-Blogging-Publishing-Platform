"use client"

import { useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Bot } from "lucide-react"
import { AppShell } from "@/features/app/app-shell"
import { AiPipeline, ANNA_PIPELINE } from "@/features/app/ai-pipeline"
import { CopyButton } from "@/features/app/copy-button"
import { Button } from "@/components/ui/button"
import { AI_WAIT_MS, api, isRetryableAiStatus, readError, sleep, type Paginated, type Post } from "@/lib/api"

type ReviewRun = {
  id: string
  status: string
  notes: string
  error_message: string
  post: Post | null
  conversation_id?: string | null
  review_message_id?: string | null
}

export function AnnaPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const requestedPost = searchParams.get("post")
  const [posts, setPosts] = useState<Post[]>([])
  const [postId, setPostId] = useState(requestedPost ?? "")
  const [pending, setPending] = useState(false)
  const [handoffPending, setHandoffPending] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  const [run, setRun] = useState<ReviewRun | null>(null)

  async function handoff() {
    if (!run?.review_message_id) return
    setHandoffPending(true)
    setNotice(null)
    try {
      const response = await api(`/api/v1/ai/anna/messages/${run.review_message_id}/continue-in-composer/`, { method: "POST", body: "{}" })
      if (!response.ok) {
        setNotice(await readError(response, "Could not start Composer from this review."))
        return
      }
      const body = (await response.json()) as { id?: string }
      router.push(body?.id ? `/compose?conversation=${body.id}` : "/compose")
    } catch {
      setNotice("The API is not reachable.")
    } finally {
      setHandoffPending(false)
    }
  }

  useEffect(() => {
    api("/api/v1/drafts/?page_size=50")
      .then(async (response) => {
        if (!response.ok) return
        const next = ((await response.json()) as Paginated<Post>).results
        setPosts(next)
        if (!requestedPost && next[0]) setPostId(String(next[0].id))
      })
      .catch(() => setNotice("The API is not reachable."))
  }, [requestedPost])

  useEffect(() => {
    if (!postId) return
    void api(`/api/v1/ai/reviews/?post_id=${postId}`)
      .then(async (response) => {
        if (!response.ok) return
        const body = (await response.json()) as { run: ReviewRun | null }
        setRun(body.run)
      })
      .catch(() => null)
  }, [postId])

  useEffect(() => {
    if (run?.status !== "queued" && run?.status !== "running") return
    const poll = window.setInterval(() => {
      void api(`/api/v1/ai/reviews/?post_id=${postId}`)
        .then(async (response) => {
          if (!response.ok) return
          const body = (await response.json()) as { run: ReviewRun | null }
          setRun(body.run)
        })
        .catch(() => null)
    }, 2500)
    return () => window.clearInterval(poll)
  }, [postId, run?.status])

  async function waitForAnnaReview(targetPostId: string) {
    const deadline = Date.now() + AI_WAIT_MS
    while (Date.now() < deadline) {
      await sleep(2000)
      try {
        const response = await api(`/api/v1/ai/reviews/?post_id=${targetPostId}`)
        if (!response.ok) continue
        const body = (await response.json()) as { run: ReviewRun | null }
        if (!body.run) continue
        if (body.run.status === "queued" || body.run.status === "running") continue
        return body.run
      } catch {
        continue
      }
    }
    return null
  }

  async function review(event: React.FormEvent) {
    event.preventDefault()
    if (!postId) {
      setNotice("Choose a saved draft first.")
      return
    }
    setPending(true)
    setNotice(null)
    setRun(null)
    try {
      const response = await api("/api/v1/ai/reviews/", {
        method: "POST",
        body: JSON.stringify({ post_id: Number(postId) }),
      })
      if (response.ok) {
        setRun((await response.json()) as ReviewRun)
        return
      }
      if (isRetryableAiStatus(response.status)) {
        const recovered = await waitForAnnaReview(postId)
        if (recovered) {
          setRun(recovered)
          return
        }
      }
      setNotice(await readError(response, "Anna could not finish that review."))
    } catch {
      const recovered = await waitForAnnaReview(postId)
      if (recovered) {
        setRun(recovered)
        return
      }
      setNotice("Anna is still reviewing. Stay on this page — the notes should appear without a refresh.")
    } finally {
      setPending(false)
    }
  }

  const selected = posts.find((post) => String(post.id) === String(postId))

  return (
    <AppShell eyebrow="Anna" title="Review a draft. She never publishes.">
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_18rem]">
        <section className="rounded-3xl border bg-card p-6 shadow-sm md:p-8">
          <div className="flex items-center gap-2">
            <span className="flex size-9 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <Bot className="size-4" />
            </span>
            <p className="text-xs font-medium tracking-[0.16em] text-primary uppercase">Draft review</p>
          </div>
          <form className="mt-5" onSubmit={review}>
            <label className="text-xs font-medium">
              Draft
              <select className="editor-input mt-2" value={postId} onChange={(event) => setPostId(event.target.value)}>
                <option value="">Choose a draft</option>
                {posts.map((post) => (
                  <option key={post.id} value={post.id}>
                    {post.title || "Untitled"}
                  </option>
                ))}
              </select>
            </label>
            {selected ? (
              <p className="mt-3 line-clamp-3 text-sm leading-6 text-muted-foreground">{selected.excerpt || selected.body}</p>
            ) : null}
            <Button className="mt-4 rounded-xl" disabled={pending || !postId} type="submit">
              {pending ? "Reviewing…" : "Review with Anna"}
            </Button>
          </form>
          {pending || run?.status === "queued" || run?.status === "running" ? <div className="mt-6"><AiPipeline steps={ANNA_PIPELINE} /></div> : null}
          {notice ? (
            <p role="status" className="mt-4 rounded-xl border border-destructive/30 bg-destructive/8 px-3 py-2 text-sm">
              {notice}
            </p>
          ) : null}
          {run?.notes ? (
            <article className="mt-6 rounded-2xl border bg-muted/30 p-5">
              <div className="flex items-center justify-between gap-3">
                <h2 className="font-medium">Anna&apos;s notes</h2>
                <div className="flex gap-2">
                  <CopyButton text={run.notes} label="Copy review" />
                  {run.review_message_id ? (
                    <Button variant="outline" className="rounded-xl" disabled={handoffPending} onClick={() => void handoff()}>
                      {handoffPending ? "Opening Composer…" : "Continue in Composer"}
                    </Button>
                  ) : null}
                </div>
              </div>
              <div className="mt-4 whitespace-pre-wrap text-sm leading-7">{run.notes}</div>
            </article>
          ) : null}
        </section>
        <aside className="rounded-3xl border bg-card p-5 text-sm leading-6 text-muted-foreground">
          Anna reads the draft you already saved. She returns strengths, gaps, and suggested edits. The post stays private until you publish it.
        </aside>
      </div>
    </AppShell>
  )
}
