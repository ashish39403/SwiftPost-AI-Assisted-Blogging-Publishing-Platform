"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { api, mediaUrl, type Category, type Paginated, type Post } from "@/lib/api"

export function DiscoverPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const category = searchParams.get("category") ?? ""
  const [posts, setPosts] = useState<Post[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [search, setSearch] = useState("")
  const [ready, setReady] = useState(false)
  const [debouncedSearch, setDebouncedSearch] = useState("")

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(search.trim()), 300)
    return () => window.clearTimeout(timer)
  }, [search])

  useEffect(() => {
    const params = new URLSearchParams()
    if (debouncedSearch) params.set("search", debouncedSearch)
    if (category) params.set("category", category)
    const query = params.toString()
    Promise.all([
      api(`/api/v1/blogs/${query ? `?${query}` : ""}`),
      api("/api/v1/categories/"),
    ])
      .then(async ([postResponse, categoryResponse]) => {
        setPosts(postResponse.ok ? ((await postResponse.json()) as Paginated<Post>).results : [])
        if (categoryResponse.ok) {
          const body = await categoryResponse.json()
          setCategories(Array.isArray(body) ? body : body?.results ?? [])
        }
        setReady(true)
      })
      .catch(() => setReady(true))
  }, [debouncedSearch, category])

  const filters = useMemo(() => [{ slug: "", name: "All" }, ...categories], [categories])

  function setCategory(slug: string) {
    const params = new URLSearchParams(searchParams.toString())
    if (slug) params.set("category", slug)
    else params.delete("category")
    const query = params.toString()
    router.replace(query ? `/discover?${query}` : "/discover")
  }

  return (
    <main id="content" className="mx-auto w-full max-w-7xl px-5 py-14 md:px-8">
      <p className="text-[11px] font-medium tracking-[.18em] text-primary uppercase">Discover</p>
      <h1 className="mt-3 font-heading text-5xl tracking-tight">Ideas with room to breathe.</h1>
      <p className="mt-3 max-w-xl text-sm leading-6 text-muted-foreground">
        Published stories from SwiftPost authors. Drafts stay private until the author publishes them.
      </p>
      <div className="mt-8 flex flex-col gap-3 md:flex-row md:items-center">
        <input
          className="auth-input max-w-sm"
          placeholder="Search published stories"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <div className="flex gap-2 overflow-x-auto">
          {filters.map((item) => (
            <button
              key={item.slug || "all"}
              type="button"
              onClick={() => setCategory(item.slug)}
              className={`shrink-0 rounded-full border px-3 py-1.5 text-xs ${category === item.slug ? "bg-primary text-primary-foreground" : "bg-card"}`}
            >
              {item.name}
            </button>
          ))}
        </div>
      </div>
      <div className="mt-8 grid gap-5 md:grid-cols-2">
        {!ready ? <p className="text-sm text-muted-foreground">Loading stories…</p> : null}
        {ready && posts.length === 0 ? (
          <p className="rounded-2xl border bg-card px-5 py-8 text-sm text-muted-foreground">
            No published stories yet. Write a draft, then click Publish. After that, anyone can read it here.
          </p>
        ) : null}
        {posts.map((post) => (
          <Link key={post.id} href={`/posts/${post.slug}`} className="story-card overflow-hidden rounded-2xl border bg-card">
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
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{post.excerpt}</p>
              <p className="mt-4 text-xs text-muted-foreground">
                {post.author.username}
                {post.published_at ? ` · ${new Date(post.published_at).toLocaleDateString()}` : ""}
                {` · ${post.like_count ?? 0} likes · ${post.comment_count ?? 0} comments`}
              </p>
            </div>
          </Link>
        ))}
      </div>
    </main>
  )
}
