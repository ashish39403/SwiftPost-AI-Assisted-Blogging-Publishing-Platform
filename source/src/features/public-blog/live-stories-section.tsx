"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { ArrowRight } from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { api, mediaUrl, type Category, type Paginated, type Post } from "@/lib/api"
import { Reveal } from "@/features/public-blog/reveal"

function initials(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  return name.slice(0, 2).toUpperCase() || "SP"
}

function rankPosts(posts: Post[]) {
  return [...posts].sort((a, b) => {
    const likes = (b.like_count ?? 0) - (a.like_count ?? 0)
    if (likes !== 0) return likes
    return (b.published_at || "").localeCompare(a.published_at || "")
  })
}

function Cover({ post, className }: { post: Post; className: string }) {
  if (post.featured_image?.url) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img src={mediaUrl(post.featured_image.url)} alt="" className={className} />
    )
  }
  return <div className={`bg-muted ${className}`} />
}

export function LiveStoriesSection() {
  const [posts, setPosts] = useState<Post[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [ready, setReady] = useState(false)

  useEffect(() => {
    Promise.all([
      api("/api/v1/blogs/?page_size=20"),
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
  }, [])

  const ranked = useMemo(() => rankPosts(posts), [posts])
  const featured = ranked[0]
  const rest = ranked.slice(1, 4)
  const shelves = useMemo(() => {
    return categories
      .map((category) => ({
        category,
        stories: ranked.filter((post) => post.category?.slug === category.slug).slice(0, 2),
      }))
      .filter((shelf) => shelf.stories.length > 0)
      .slice(0, 3)
  }, [categories, ranked])

  return (
    <>
      <section id="stories" className="scroll-mt-24 border-t">
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-5 py-16 md:px-8 md:py-20">
          <Reveal>
            <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
              <div className="max-w-sm">
                <h2 className="font-heading text-4xl tracking-tight">Featured stories</h2>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  Live posts from SwiftPost authors. Drafts stay private until someone publishes.
                </p>
              </div>
              <Link href="/discover" className="inline-flex items-center gap-1 text-sm text-primary">
                Explore all stories
                <ArrowRight aria-hidden="true" className="size-4" />
              </Link>
            </div>
          </Reveal>
          {!ready ? <p className="text-sm text-muted-foreground">Loading published stories…</p> : null}
          {ready && ranked.length === 0 ? (
            <p className="rounded-2xl border bg-card px-5 py-8 text-sm text-muted-foreground">
              No published stories yet. When an author clicks Publish, the post appears here and on Discover.
            </p>
          ) : null}
          {featured ? (
            <div className="grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
              <Reveal>
                <Link href={`/posts/${featured.slug}`} className="story-card flex h-full flex-col gap-4 overflow-hidden rounded-2xl bg-card ring-1 ring-foreground/8 md:flex-row">
                  <div className="relative aspect-[4/3] min-h-48 overflow-hidden md:w-[46%]">
                    <Cover post={featured} className="absolute inset-0 size-full object-cover" />
                  </div>
                  <div className="flex min-w-0 flex-1 flex-col gap-3 p-5">
                    <Badge variant="secondary">{featured.category?.name ?? "Uncategorized"}</Badge>
                    <h3 className="font-heading text-2xl leading-snug tracking-tight">{featured.title || "Untitled"}</h3>
                    <p className="text-sm leading-6 text-muted-foreground">{featured.excerpt}</p>
                    <div className="mt-auto flex items-center gap-2">
                      <Avatar size="sm">
                        <AvatarFallback>{initials(featured.author.username)}</AvatarFallback>
                      </Avatar>
                      <p className="text-xs text-muted-foreground">
                        By {featured.author.username}
                        {` · ${featured.like_count ?? 0} likes`}
                      </p>
                    </div>
                  </div>
                </Link>
              </Reveal>
              <div className="flex flex-col gap-4">
                {rest.map((story, index) => (
                  <Reveal key={story.id} delay={index * 50}>
                    <Link href={`/posts/${story.slug}`} className="story-card flex gap-4 overflow-hidden rounded-2xl bg-card ring-1 ring-foreground/8">
                      <div className="relative size-28 shrink-0 overflow-hidden sm:size-32">
                        <Cover post={story} className="absolute inset-0 size-full object-cover" />
                      </div>
                      <div className="flex min-w-0 flex-col gap-2 py-4 pr-4">
                        <p className="text-[11px] font-medium tracking-wide text-primary uppercase">
                          {story.category?.name ?? "Uncategorized"}
                        </p>
                        <h3 className="font-heading text-lg leading-snug tracking-tight">{story.title || "Untitled"}</h3>
                        <p className="hidden text-sm leading-5 text-muted-foreground sm:block">{story.excerpt}</p>
                        <p className="mt-auto text-xs text-muted-foreground">By {story.author.username}</p>
                      </div>
                    </Link>
                  </Reveal>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </section>

      {shelves.length > 0 ? (
        <section className="scroll-mt-24 border-t bg-muted/35" aria-labelledby="explore-heading">
          <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-5 py-16 md:px-8 md:py-20">
            <Reveal>
              <div className="max-w-xl">
                <p className="text-[11px] font-medium tracking-[0.18em] text-primary uppercase">Explore by subject</p>
                <h2 id="explore-heading" className="mt-3 font-heading text-4xl tracking-tight">More ways into a good story.</h2>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">Published posts grouped by the categories authors actually used.</p>
              </div>
            </Reveal>
            <div className="grid gap-5 lg:grid-cols-3">
              {shelves.map((shelf, shelfIndex) => (
                <Reveal key={shelf.category.slug} delay={shelfIndex * 60}>
                  <section className="flex h-full flex-col gap-4 rounded-2xl bg-card p-4 ring-1 ring-foreground/8">
                    <header className="border-b border-border pb-3">
                      <p className="text-[11px] font-medium tracking-[0.18em] text-primary uppercase">{shelf.category.name}</p>
                      <p className="mt-1 text-sm leading-5 text-muted-foreground">
                        {shelf.category.description || "Live stories in this category."}
                      </p>
                    </header>
                    <div className="flex flex-col gap-4">
                      {shelf.stories.map((story) => (
                        <Link key={story.id} href={`/posts/${story.slug}`} className="story-card group flex gap-3 rounded-xl p-1">
                          <div className="story-image relative size-20 shrink-0 overflow-hidden rounded-lg">
                            <Cover post={story} className="absolute inset-0 size-full object-cover" />
                          </div>
                          <div className="min-w-0 py-0.5">
                            <h3 className="font-heading text-lg leading-snug tracking-tight">{story.title || "Untitled"}</h3>
                            <p className="mt-1 text-xs text-muted-foreground">By {story.author.username}</p>
                          </div>
                        </Link>
                      ))}
                    </div>
                    <Link href={`/discover?category=${shelf.category.slug}`} className="mt-auto text-sm text-primary">
                      See all in {shelf.category.name}
                    </Link>
                  </section>
                </Reveal>
              ))}
            </div>
          </div>
        </section>
      ) : null}
    </>
  )
}
