"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { AppShell } from "@/features/app/app-shell"
import { api, type Paginated, type Post } from "@/lib/api"

export function AdminPage() {
  const [posts, setPosts] = useState<Post[]>([])
  const [notice, setNotice] = useState<string | null>(null)

  function load() {
    api("/api/v1/drafts/?status=published&page_size=50")
      .then(async (response) => {
        if (!response.ok) {
          setPosts([])
          return
        }
        setPosts(((await response.json()) as Paginated<Post>).results)
      })
      .catch(() => setPosts([]))
  }

  useEffect(() => {
    load()
  }, [])

  async function unpublish(id: number) {
    const response = await api(`/api/v1/blogs/${id}/unpublish/`, { method: "POST", body: "{}" })
    if (!response.ok) {
      setNotice("Could not unpublish that story.")
      return
    }
    setNotice("Taken down.")
    load()
  }

  return (
    <AppShell eyebrow="Moderation" title="Take down anything that should not stay live.">
      {notice ? <p className="mb-4 text-sm text-muted-foreground">{notice}</p> : null}
      <div className="grid gap-5 md:grid-cols-3">
        <Metric value={String(posts.length)} label="Live stories you can unpublish" />
      </div>
      <section className="mt-8 rounded-2xl border bg-card">
        <div className="border-b px-5 py-4"><h2 className="font-heading text-2xl">Live stories</h2></div>
        {posts.length === 0 ? <p className="px-5 py-8 text-sm text-muted-foreground">Nothing is live right now.</p> : null}
        {posts.map((post) => (
          <div key={post.id} className="app-row mx-3 border-b last:border-0">
            <span>
              <span className="font-medium">{post.title || "Untitled"}</span>
              <span className="mt-1 block text-xs text-muted-foreground">{post.author.username} · {post.status}</span>
            </span>
            <Button variant="outline" size="sm" onClick={() => void unpublish(post.id)}>Unpublish</Button>
          </div>
        ))}
      </section>
    </AppShell>
  )
}

function Metric({ value, label }: { value: string; label: string }) {
  return (
    <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
      <p className="text-xs font-medium tracking-[0.14em] text-muted-foreground uppercase">{label}</p>
      <p className="mt-3 font-heading text-4xl tracking-tight">{value}</p>
    </div>
  )
}
