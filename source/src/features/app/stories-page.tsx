"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { FilePenLine, Plus } from "lucide-react"
import { AppShell } from "@/features/app/app-shell"
import { Button } from "@/components/ui/button"
import { api, type Paginated, type Post } from "@/lib/api"

const STATUS_LABEL: Record<string, string> = {
  draft: "Draft",
  in_review: "In review",
  published: "Published",
  unpublished: "Unpublished",
  changes_requested: "Changes requested",
  archived: "Archived",
}

export function StoriesPage() {
  const searchParams = useSearchParams()
  const [posts, setPosts] = useState<Post[]>([])
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const query = searchParams.get("search")?.trim()
    api(`/api/v1/drafts/?page_size=50${query ? `&search=${encodeURIComponent(query)}` : ""}`)
      .then(async (response) => {
        setPosts(response.ok ? (((await response.json()) as Paginated<Post>).results ?? []) : [])
        setReady(true)
      })
      .catch(() => setReady(true))
  }, [searchParams])

  return (
    <AppShell eyebrow="Stories" title="Every draft and published post in one list.">
      <div className="mb-6 flex justify-end">
        <Button asChild className="rounded-xl">
          <Link href="/editor/new">
            <Plus data-icon="inline-start" />
            New story
          </Link>
        </Button>
      </div>
      {searchParams.get("search") ? <p className="mb-4 text-sm text-muted-foreground">Results for “{searchParams.get("search")}”</p> : null}
      <section className="rounded-3xl border bg-card">
        {!ready ? <p className="px-5 py-8 text-sm text-muted-foreground">Loading your stories…</p> : null}
        {ready && posts.length === 0 ? (
          <p className="px-5 py-8 text-sm text-muted-foreground">
            Nothing here yet. Write a draft or ask Composer for a first version.
          </p>
        ) : null}
        {posts.map((post) => (
          <Link key={post.id} href={`/editor/${post.id}`} className="app-row mx-3 border-b last:border-0">
            <span>
              <span className="font-medium">{post.title || "Untitled"}</span>
              <span className="mt-1 block text-xs text-muted-foreground">
                {STATUS_LABEL[post.status] ?? post.status}
                {post.category?.name ? ` · ${post.category.name}` : ""}
              </span>
            </span>
            <span className="inline-flex items-center gap-1 text-sm text-primary">
              <FilePenLine className="size-4" />
              Open editor
            </span>
          </Link>
        ))}
      </section>
    </AppShell>
  )
}
