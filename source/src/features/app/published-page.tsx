"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Eye, Heart, MessageCircle } from "lucide-react"
import { AppShell } from "@/features/app/app-shell"
import { api, mediaUrl, type Paginated, type Post } from "@/lib/api"

export function PublishedPage() {
  const [posts, setPosts] = useState<Post[]>([])
  const [ready, setReady] = useState(false)

  useEffect(() => {
    api("/api/v1/drafts/?status=published&page_size=50")
      .then(async (response) => {
        setPosts(response.ok ? (((await response.json()) as Paginated<Post>).results ?? []) : [])
        setReady(true)
      })
      .catch(() => setReady(true))
  }, [])

  return (
    <AppShell eyebrow="Published" title="Stories that are live.">
      <p className="max-w-xl text-sm leading-6 text-muted-foreground">
        These are your published posts. Open any story to view it, like it, or read comments.
        Anyone who is signed in can comment on a live story. Comments show up immediately.
      </p>
      <section className="mt-8">
        {!ready ? <p className="text-sm text-muted-foreground">Loading published stories…</p> : null}
        {ready && posts.length === 0 ? (
          <p className="rounded-2xl border bg-card px-5 py-8 text-sm leading-6 text-muted-foreground">
            Nothing is live yet. Open a story and publish it when you are ready.
          </p>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {posts.map((post) => (
              <article key={post.id} className="story-card overflow-hidden rounded-2xl border bg-card">
                {post.featured_image ? (
                  <div className="relative aspect-[16/8] overflow-hidden bg-muted">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={mediaUrl(post.featured_image.url)} alt="" className="h-full w-full object-cover" />
                  </div>
                ) : (
                  <div className="aspect-[16/8] bg-muted" />
                )}
                <div className="p-5">
                  <p className="text-xs font-medium text-primary">{post.category?.name ?? "Uncategorized"}</p>
                  <h2 className="mt-2 font-heading text-2xl">{post.title || "Untitled"}</h2>
                  <p className="mt-2 line-clamp-2 text-sm leading-6 text-muted-foreground">{post.excerpt}</p>
                  <p className="mt-4 flex flex-wrap gap-3 text-xs text-muted-foreground">
                    <span className="inline-flex items-center gap-1"><Heart className="size-3.5" />{post.like_count ?? 0} likes</span>
                    <span className="inline-flex items-center gap-1"><MessageCircle className="size-3.5" />{post.comment_count ?? 0} comments</span>
                  </p>
                  <Link href={`/posts/${post.slug}`} className="mt-4 inline-flex items-center gap-1 text-sm text-primary">
                    <Eye className="size-4" />
                    View story
                  </Link>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </AppShell>
  )
}
