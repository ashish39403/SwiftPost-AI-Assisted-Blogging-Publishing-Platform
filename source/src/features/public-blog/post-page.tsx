"use client"

import { useEffect, useState } from "react"
import { PostEngagement } from "@/features/public-blog/post-engagement"
import { api, mediaUrl, type Post } from "@/lib/api"

export function PostPage({ slug }: { slug: string }) {
  const [post, setPost] = useState<Post | null>(null)
  const [missing, setMissing] = useState(false)

  useEffect(() => {
    api(`/api/v1/blogs/${slug}/`)
      .then(async (response) => {
        if (!response.ok) {
          setMissing(true)
          return
        }
        setPost((await response.json()) as Post)
      })
      .catch(() => setMissing(true))
  }, [slug])

  if (missing) {
    return (
      <main id="content" className="mx-auto w-full max-w-3xl px-5 py-16 md:px-8">
        <h1 className="font-heading text-4xl">Story not found</h1>
        <p className="mt-3 text-sm text-muted-foreground">This article is not published, or the link is no longer valid.</p>
      </main>
    )
  }

  if (!post) {
    return (
      <main id="content" className="mx-auto w-full max-w-3xl px-5 py-16 md:px-8">
        <p className="text-sm text-muted-foreground">Loading story…</p>
      </main>
    )
  }

  return (
    <main id="content" className="mx-auto w-full max-w-4xl px-5 py-12 md:px-8">
      <p className="text-xs font-medium text-primary">{post.category?.name ?? "Uncategorized"}</p>
      <h1 className="mt-3 font-heading text-5xl leading-tight tracking-tight">{post.title}</h1>
      <p className="mt-4 text-lg leading-8 text-muted-foreground">{post.excerpt}</p>
      <p className="mt-5 text-sm text-muted-foreground">
        By {post.author.username}
        {post.published_at ? ` · ${new Date(post.published_at).toLocaleDateString()}` : ""}
      </p>
      {post.featured_image ? (
        <div className="relative mt-8 overflow-hidden rounded-2xl">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={mediaUrl(post.featured_image.url)} alt="" className="w-full object-cover" />
        </div>
      ) : null}
      <article className="prose-like mt-10 max-w-2xl whitespace-pre-wrap text-[1.05rem] leading-8 text-foreground">
        {post.body}
      </article>
      {post.images.length > 1 ? (
        <section className="mt-10" aria-label="Story images">
          <h2 className="font-heading text-2xl">More from this story</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {post.images.slice(1).map((image) => (
              <div key={image.id} className="overflow-hidden rounded-2xl border bg-card">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={mediaUrl(image.url)} alt="" className="aspect-[16/10] w-full object-cover" />
              </div>
            ))}
          </div>
        </section>
      ) : null}
      <PostEngagement key={post.id} post={post} />
    </main>
  )
}
