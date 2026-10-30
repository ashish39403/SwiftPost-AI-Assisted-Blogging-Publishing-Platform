"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Heart, MessageCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { api, readError, type Account, type CommentItem, type Paginated, type Post } from "@/lib/api"

export function PostEngagement({ post }: { post: Post }) {
  const [account, setAccount] = useState<Account | null | undefined>(undefined)
  const [liked, setLiked] = useState(post.liked)
  const [likeCount, setLikeCount] = useState(post.like_count ?? 0)
  const [comments, setComments] = useState<CommentItem[]>([])
  const [approvedAdded, setApprovedAdded] = useState(0)
  const [body, setBody] = useState("")
  const [notice, setNotice] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  useEffect(() => {
    api("/api/v1/auth/me/")
      .then(async (response) => {
        setAccount(response.ok ? ((await response.json()) as { user: Account }).user : null)
      })
      .catch(() => setAccount(null))
    api(`/api/v1/blogs/${post.id}/comments/?page_size=50`)
      .then(async (response) => {
        if (response.ok) setComments(((await response.json()) as Paginated<CommentItem>).results ?? [])
      })
      .catch(() => null)
  }, [post.id])

  async function toggleLike() {
    if (!account) {
      setNotice("Sign in to like this story.")
      return
    }
    const response = await api(`/api/v1/blogs/${post.id}/likes/`, { method: "POST", body: "{}" })
    if (!response.ok) {
      setNotice(await readError(response, "Could not update the like."))
      return
    }
    const next = (await response.json()) as { liked: boolean; count: number }
    setLiked(next.liked)
    setLikeCount(next.count)
  }

  async function submitComment(event: React.FormEvent) {
    event.preventDefault()
    if (!account) {
      setNotice("Sign in to comment.")
      return
    }
    setPending(true)
    setNotice(null)
    try {
      const response = await api(`/api/v1/blogs/${post.id}/comments/`, {
        method: "POST",
        body: JSON.stringify({ body }),
      })
      if (!response.ok) {
        setNotice(await readError(response, "Could not post that comment."))
        return
      }
      const comment = (await response.json()) as CommentItem
      setBody("")
      setComments((current) => [...current, comment])
      setApprovedAdded((current) => current + 1)
      setNotice("Comment posted.")
    } catch {
      setNotice("The API is not reachable.")
    } finally {
      setPending(false)
    }
  }

  return (
    <section className="mt-12 max-w-2xl border-t pt-8">
      <div className="flex flex-wrap items-center gap-3">
        <Button type="button" variant={liked ? "default" : "outline"} onClick={() => void toggleLike()}>
          <Heart data-icon="inline-start" className={liked ? "fill-current" : ""} />
          {liked ? "Liked" : "Like"} · {likeCount}
        </Button>
        <span className="inline-flex items-center gap-1 text-sm text-muted-foreground">
          <MessageCircle className="size-4" />
          {(post.comment_count ?? 0) + approvedAdded} comments
        </span>
      </div>
      {notice ? <p className="mt-4 text-sm text-muted-foreground">{notice}</p> : null}
      <form onSubmit={submitComment} className="mt-6">
        <label className="text-xs font-medium">
          Comment
          <textarea
            className="editor-input mt-2 min-h-24 resize-y"
            value={body}
            onChange={(event) => setBody(event.target.value)}
            placeholder={account ? "Share a thought about this story." : "Sign in to comment."}
            maxLength={2000}
            disabled={!account}
          />
        </label>
        <div className="mt-3 flex flex-wrap gap-3">
          <Button type="submit" disabled={pending || !account || !body.trim()}>
            {pending ? "Posting…" : "Post comment"}
          </Button>
          {!account ? (
            <Button asChild variant="outline">
              <Link href="/login">Sign in</Link>
            </Button>
          ) : null}
        </div>
      </form>
      <ul className="mt-8 space-y-4">
        {comments.length === 0 ? (
          <li className="text-sm text-muted-foreground">No public comments yet.</li>
        ) : (
          comments.map((comment) => (
            <li key={comment.id} className="rounded-2xl border bg-card p-4">
              <p className="text-xs font-medium">{comment.author.username}</p>
              <p className="mt-2 text-sm leading-6 whitespace-pre-wrap">{comment.body}</p>
            </li>
          ))
        )}
      </ul>
    </section>
  )
}
