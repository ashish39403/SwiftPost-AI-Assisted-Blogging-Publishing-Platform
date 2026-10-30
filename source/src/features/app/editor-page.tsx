"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { AppShell } from "@/features/app/app-shell"
import { FeaturedImagePanel } from "@/features/app/featured-image-panel"
import { Button } from "@/components/ui/button"
import { api, readError, type Category, type Post } from "@/lib/api"

export function EditorPage({ postId }: { postId?: string }) {
  const router = useRouter()
  const isNew = !postId || postId === "new"
  const [post, setPost] = useState<Post | null>(null)
  const [categories, setCategories] = useState<Category[]>([])
  const [title, setTitle] = useState("")
  const [excerpt, setExcerpt] = useState("")
  const [body, setBody] = useState("")
  const [categoryId, setCategoryId] = useState<number | "">("")
  const [notice, setNotice] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  useEffect(() => {
    api("/api/v1/categories/?page_size=50")
      .then(async (response) => {
        if (!response.ok) return
        const payload = await response.json()
        const list = Array.isArray(payload) ? payload : payload?.results ?? []
        setCategories(list as Category[])
      })
      .catch(() => null)
  }, [])

  useEffect(() => {
    if (isNew) return
    api(`/api/v1/drafts/${postId}/`)
      .then(async (response) => {
        if (!response.ok) {
          setNotice(await readError(response, "This draft could not be opened."))
          return
        }
        const next = (await response.json()) as Post
        setPost(next)
        setTitle(next.title)
        setExcerpt(next.excerpt)
        setBody(next.body)
        setCategoryId(next.category?.id ?? "")
      })
      .catch(() => setNotice("The API is not reachable."))
  }, [isNew, postId])

  const live = post?.status === "published"
  const canEdit = !post || ["draft", "changes_requested", "unpublished"].includes(post.status)

  async function save() {
    setPending(true)
    setNotice(null)
    const payload = {
      title,
      excerpt,
      body,
      category_id: categoryId === "" ? null : categoryId,
    }
    try {
      const response = await api(isNew ? "/api/v1/drafts/" : `/api/v1/drafts/${post?.id ?? postId}/`, {
        method: isNew ? "POST" : "PATCH",
        body: JSON.stringify(payload),
      })
      if (!response.ok) {
        setNotice(await readError(response, "Could not save the draft."))
        return null
      }
      const saved = (await response.json()) as Post
      setPost(saved)
      if (isNew) router.replace(`/editor/${saved.id}`)
      setNotice("Draft saved.")
      return saved
    } catch {
      setNotice("The API is not reachable.")
      return null
    } finally {
      setPending(false)
    }
  }

  async function publish() {
    const saved = canEdit ? await save() : post
    if (!saved) return
    const response = await api(`/api/v1/blogs/${saved.id}/publish/`, { method: "POST", body: "{}" })
    if (!response.ok) {
      setNotice(await readError(response, "Could not publish the story."))
      return
    }
    setPost((await response.json()) as Post)
    setNotice("Published. Readers can open it on Discover.")
  }

  async function unpublish() {
    if (!post) return
    setPending(true)
    try {
      const response = await api(`/api/v1/blogs/${post.id}/unpublish/`, { method: "POST", body: "{}" })
      if (!response.ok) {
        setNotice(await readError(response, "Could not unpublish the story."))
        return
      }
      setPost((await response.json()) as Post)
      setNotice("Unpublished. The story is private again.")
    } finally {
      setPending(false)
    }
  }

  return (
    <AppShell eyebrow="Editor" title={isNew ? "Start a new draft" : title || "Untitled draft"}>
      {notice ? <p role="status" className="mb-4 text-sm text-muted-foreground">{notice}</p> : null}
      <div className="grid gap-6 lg:grid-cols-[1fr_18rem]">
        <section className="rounded-2xl border bg-card p-5">
          <label className="text-xs font-medium">
            Title
            <input className="editor-input mt-2 text-xl font-heading" value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Give your story a clear title" disabled={!canEdit} />
          </label>
          <label className="mt-5 block text-xs font-medium">
            Opening
            <input className="editor-input mt-2" value={excerpt} onChange={(event) => setExcerpt(event.target.value)} placeholder="What should readers know first?" disabled={!canEdit} />
          </label>
          <label className="mt-5 block text-xs font-medium">
            Article body
            <textarea className="editor-input mt-2 min-h-64 resize-y" value={body} onChange={(event) => setBody(event.target.value)} placeholder="Write the story." disabled={!canEdit} />
          </label>
          <div className="mt-5 flex flex-wrap gap-3">
            {canEdit ? <Button type="button" onClick={() => void save()} disabled={pending}>{pending ? "Saving…" : "Save draft"}</Button> : null}
            {live ? (
              <Button type="button" variant="outline" onClick={() => void unpublish()} disabled={pending}>Unpublish</Button>
            ) : (
              <Button type="button" variant="outline" onClick={() => void publish()} disabled={pending}>Publish</Button>
            )}
            {post ? (
              <Button type="button" variant="outline" asChild>
                <a href={`/anna?post=${post.id}`}>Review with Anna</a>
              </Button>
            ) : null}
          </div>
        </section>
        <aside className="space-y-4">
          <section className="rounded-2xl border bg-card p-4">
            <h2 className="font-medium">Category</h2>
            <select
              className="editor-input mt-3"
              value={categoryId === "" ? "" : String(categoryId)}
              onChange={(event) => setCategoryId(event.target.value ? Number(event.target.value) : "")}
              disabled={!canEdit}
            >
              <option value="">Choose a category</option>
              {categories.map((item) => (
                <option key={item.id} value={item.id}>{item.name}</option>
              ))}
            </select>
            {categories.length === 0 ? (
              <p className="mt-2 text-xs text-muted-foreground">No categories available yet.</p>
            ) : null}
            <p className="mt-3 text-xs text-muted-foreground">Status: {(post?.status ?? "draft").replaceAll("_", " ")}</p>
            {!canEdit ? <p className="mt-2 text-xs text-muted-foreground">This story is read-only until its status changes.</p> : null}
          </section>
          {canEdit ? <FeaturedImagePanel key={post?.id ?? "new"} post={post} query={title} allowMultiple onUpdated={setPost} onNotice={setNotice} /> : null}
        </aside>
      </div>
    </AppShell>
  )
}
