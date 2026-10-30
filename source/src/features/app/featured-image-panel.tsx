"use client"

import { useEffect, useRef, useState } from "react"
import { ImagePlus, Search } from "lucide-react"
import { Button } from "@/components/ui/button"
import { api, mediaUrl, readError, type ImageSuggestion, type Post } from "@/lib/api"

const EMPTY_SUGGESTIONS: ImageSuggestion[] = []

export function FeaturedImagePanel({
  post,
  query,
  initialSuggestions = EMPTY_SUGGESTIONS,
  allowMultiple = false,
  onUpdated,
  onNotice,
  onSuggestions,
}: {
  post: Post | null
  query: string
  initialSuggestions?: ImageSuggestion[]
  allowMultiple?: boolean
  onUpdated: (post: Post) => void
  onNotice: (message: string) => void
  onSuggestions?: (items: ImageSuggestion[]) => void
}) {
  const fileRef = useRef<HTMLInputElement>(null)
  const [suggestions, setSuggestions] = useState<ImageSuggestion[]>(initialSuggestions)
  const [picked, setPicked] = useState<number[]>(() => initialSuggestions.filter((item) => item.selected).map((item) => item.id))
  const [busy, setBusy] = useState<"upload" | "search" | "save" | number | null>(null)

  useEffect(() => {
    if (!post || initialSuggestions.length) return
    api(`/api/v1/media/search-images/?post_id=${post.id}`)
      .then(async (response) => {
        if (!response.ok) return
        const next = (await response.json()) as ImageSuggestion[]
        setSuggestions(next)
        onSuggestions?.(next)
      })
      .catch(() => null)
    // Load once per draft; parent callbacks stay fresh without retriggering search.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialSuggestions.length, post?.id])

  async function upload(file: File) {
    if (!post) {
      onNotice("Save the draft before adding an image.")
      return
    }
    setBusy("upload")
    const data = new FormData()
    data.set("post_id", String(post.id))
    data.set("file", file)
    try {
      const response = await api("/api/v1/media/upload/", { method: "POST", body: data })
      if (!response.ok) {
        onNotice(await readError(response, "Could not upload the image."))
        return
      }
      await refresh(post.id, "Featured image saved.")
    } catch {
      onNotice("The API is not reachable.")
    } finally {
      setBusy(null)
      if (fileRef.current) fileRef.current.value = ""
    }
  }

  async function searchImages() {
    if (!post) {
      onNotice("Save the draft before searching for images.")
      return
    }
    setBusy("search")
    try {
      const response = await api("/api/v1/media/search-images/", {
        method: "POST",
        body: JSON.stringify({ post_id: post.id, query }),
      })
      if (!response.ok) {
        onNotice(await readError(response, "Live image search is not available right now."))
        return
      }
      const next = (await response.json()) as ImageSuggestion[]
      setSuggestions(next)
      setPicked([])
      onSuggestions?.(next)
      onNotice(next.length ? "Select one or more images, then save." : "No live images were found. Upload a file instead.")
    } catch {
      onNotice("The API is not reachable.")
    } finally {
      setBusy(null)
    }
  }

  function toggle(id: number) {
    if (!allowMultiple) {
      void attachSuggestion(id)
      return
    }
    setPicked((current) => {
      if (current.includes(id)) return current.filter((item) => item !== id)
      if (current.length >= 2) {
        onNotice("Choose up to two images for this story.")
        return current
      }
      return [...current, id]
    })
  }

  async function attachSuggestion(id: number) {
    setBusy(id)
    try {
      const response = await api(`/api/v1/media/suggestions/${id}/attach/`, { method: "POST", body: "{}" })
      if (!response.ok) {
        onNotice(await readError(response, "That live image could not be saved."))
        return
      }
      await refresh(post!.id, "Image saved to this draft.")
    } catch {
      onNotice("The API is not reachable.")
    } finally {
      setBusy(null)
    }
  }

  async function saveSelected() {
    if (!post || picked.length === 0) {
      onNotice("Select at least one image to save.")
      return
    }
    setBusy("save")
    try {
      const response = await api("/api/v1/media/suggestions/save/", {
        method: "POST",
        body: JSON.stringify({ ids: picked }),
      })
      if (!response.ok) {
        onNotice(await readError(response, "Those images could not be saved."))
        return
      }
      await refresh(post.id, picked.length > 1 ? "Two images saved. The first is the featured image." : "Image saved to the draft.")
    } catch {
      onNotice("The API is not reachable.")
    } finally {
      setBusy(null)
    }
  }

  async function refresh(postId: number, message: string) {
    const refreshed = await api(`/api/v1/drafts/${postId}/`)
    if (refreshed.ok) onUpdated((await refreshed.json()) as Post)
    onNotice(message)
  }

  return (
    <section className="rounded-2xl border bg-card p-4">
      <h2 className="font-medium">Story images</h2>
      {post?.featured_image ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={mediaUrl(post.featured_image.url)} alt="" className="mt-3 w-full rounded-xl object-cover" />
      ) : (
        <p className="mt-2 text-xs leading-5 text-muted-foreground">
          {post ? "Composer finds images for every request. Select up to two, then save them to this draft." : "Composer creates the draft first, then relevant images appear here."}
        </p>
      )}
      <input
        ref={fileRef}
        className="sr-only"
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={(event) => {
          const file = event.target.files?.[0]
          if (file) void upload(file)
        }}
      />
      <div className="mt-3 flex flex-wrap gap-2">
        <Button type="button" variant="outline" size="sm" disabled={busy !== null || !post} onClick={() => fileRef.current?.click()}>
          <ImagePlus data-icon="inline-start" />
          {busy === "upload" ? "Uploading…" : "Upload image"}
        </Button>
        <Button type="button" variant="outline" size="sm" disabled={busy !== null || !post} onClick={() => void searchImages()}>
          <Search data-icon="inline-start" />
          {busy === "search" ? "Searching…" : "Find live images"}
        </Button>
      </div>
      {suggestions.length > 0 ? (
        <>
          <ul className="mt-4 grid grid-cols-2 gap-2">
            {suggestions.map((item) => {
              const chosen = picked.includes(item.id)
              return (
                <li key={item.id}>
                  <button
                    type="button"
                    className={`overflow-hidden rounded-xl border text-left disabled:opacity-60 ${chosen ? "ring-2 ring-primary" : ""}`}
                    disabled={busy !== null}
                    onClick={() => toggle(item.id)}
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={mediaUrl(item.image_url)} alt="" className="aspect-[16/10] w-full object-cover" />
                    <span className="block px-2 py-1.5 text-[11px] leading-4 text-muted-foreground">
                      {busy === item.id ? "Saving…" : chosen ? "Selected" : item.description || "Select"}
                    </span>
                  </button>
                </li>
              )
            })}
          </ul>
          {allowMultiple ? (
            <Button className="mt-3 w-full rounded-xl" size="sm" disabled={busy !== null || picked.length === 0} onClick={() => void saveSelected()}>
              {busy === "save" ? "Saving images…" : `Save ${picked.length} selected image${picked.length === 1 ? "" : "s"}`}
            </Button>
          ) : null}
        </>
      ) : null}
    </section>
  )
}
