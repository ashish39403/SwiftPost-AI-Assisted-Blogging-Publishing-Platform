"use client"

import { useEffect, useRef, useState } from "react"
import Link from "next/link"
import { Archive, FileText, MessageSquarePlus, Send, Sparkles, Wand2 } from "lucide-react"
import { AppShell } from "@/features/app/app-shell"
import { AiPipeline, COMPOSE_PIPELINE } from "@/features/app/ai-pipeline"
import { ComposerAnswer } from "@/features/app/composer-article"
import { FeaturedImagePanel } from "@/features/app/featured-image-panel"
import { Button } from "@/components/ui/button"
import { api, isRetryableAiStatus, readError, type AiConversation, type ImageSuggestion, type Paginated, type Post } from "@/lib/api"

type CreateResponse = { conversation: AiConversation }

const ACTIVE_KEY = "swiftpost.composerConversation"

function rememberedConversationId() {
  try {
    return window.sessionStorage.getItem(ACTIVE_KEY)
  } catch {
    return null
  }
}

function rememberConversationId(id: string | null) {
  try {
    if (id) window.sessionStorage.setItem(ACTIVE_KEY, id)
    else window.sessionStorage.removeItem(ACTIVE_KEY)
  } catch {
    return
  }
}

function syncConversationUrl(id: string | null) {
  const url = new URL(window.location.href)
  const current = url.searchParams.get("conversation")
  if (id && current === id) return
  if (!id && !current) return
  if (id) url.searchParams.set("conversation", id)
  else url.searchParams.delete("conversation")
  window.history.replaceState(window.history.state, "", `${url.pathname}${url.search}${url.hash}`)
}

export function ComposePage() {
  const [conversations, setConversations] = useState<AiConversation[]>([])
  const [active, setActive] = useState<AiConversation | null>(null)
  const [prompt, setPrompt] = useState("")
  const [pending, setPending] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  const wantedId = useRef<string | null>(null)
  const activeId = useRef<string | null>(null)

  async function loadConversations(selectId?: string) {
    const response = await api("/api/v1/ai/composer/conversations/?page_size=50")
    if (!response.ok) throw new Error("Could not load Composer history.")
    const next = ((await response.json()) as Paginated<AiConversation>).results
    setConversations(next)
    const wanted = selectId ?? wantedId.current ?? activeId.current
    const selected = wanted ? next.find((item) => item.id === wanted) : undefined
    const generating = next.find((item) => item.is_generating)
    const nextActive = selected ?? generating ?? next.find((item) => item.id === activeId.current) ?? next[0] ?? null
    setActive(nextActive)
    activeId.current = nextActive?.id ?? null
    rememberConversationId(nextActive?.id ?? null)
    if (nextActive) syncConversationUrl(nextActive.id)
  }

  useEffect(() => {
    wantedId.current = new URLSearchParams(window.location.search).get("conversation") || rememberedConversationId()
    const timer = window.setTimeout(() => {
      void loadConversations().catch(() => setNotice("The API is not reachable."))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [])

  useEffect(() => {
    if (!active?.is_generating) return
    const poll = window.setInterval(() => {
      void loadConversation(active.id)
        .then((next) => {
          if (!next) return
          applyConversation(next)
          if (!next.is_generating && next.last_error && next.messages.every((item) => item.role !== "assistant")) {
            setPending(false)
            setNotice(next.last_error)
          }
        })
        .catch(() => null)
    }, 1200)
    return () => window.clearInterval(poll)
  }, [active?.id, active?.is_generating])

  async function loadConversation(id: string) {
    const response = await api(`/api/v1/ai/composer/conversations/${id}/`)
    if (!response.ok) return null
    return (await response.json()) as AiConversation
  }

  function applyConversation(conversation: AiConversation) {
    setActive(conversation)
    activeId.current = conversation.id
    wantedId.current = conversation.id
    rememberConversationId(conversation.id)
    setConversations((items) => {
      const exists = items.some((item) => item.id === conversation.id)
      if (!exists) return [conversation, ...items]
      return items.map((item) => (item.id === conversation.id ? conversation : item))
    })
  }

  function showConversation(conversation: AiConversation) {
    setPrompt("")
    applyConversation(conversation)
    syncConversationUrl(conversation.id)
  }

  async function send(event: React.FormEvent) {
    event.preventDefault()
    const content = prompt.trim()
    if (!content) return
    const conversationId = active?.id ?? null
    setPending(true)
    setNotice(null)
    try {
      const response = conversationId
        ? await api(`/api/v1/ai/composer/conversations/${conversationId}/messages/`, {
            method: "POST",
            body: JSON.stringify({ content }),
          })
        : await api("/api/v1/ai/composer/conversations/", {
            method: "POST",
            body: JSON.stringify({ message: content }),
          })
      if (response.ok) {
        const body = (await response.json()) as AiConversation | CreateResponse
        const conversation = "conversation" in body ? body.conversation : body
        showConversation(conversation)
        return
      }
      if (isRetryableAiStatus(response.status)) {
        await loadConversations(conversationId ?? undefined)
        return
      }
      setNotice(await readError(response, "Composer could not answer that request."))
    } catch {
      await loadConversations(conversationId ?? undefined).catch(() => null)
      setNotice("Composer is writing in the background. You can leave this page and come back.")
    } finally {
      setPending(false)
    }
  }

  async function archive() {
    if (!active) return
    const response = await api(`/api/v1/ai/composer/conversations/${active.id}/archive/`, {
      method: "POST",
      body: "{}",
    })
    if (!response.ok) {
      setNotice(await readError(response, "Could not archive this chat."))
      return
    }
    setActive(null)
    activeId.current = null
    wantedId.current = null
    rememberConversationId(null)
    syncConversationUrl(null)
    await loadConversations()
  }

  const suggestions = active?.suggested_images ?? []
  const startNewChat = () => {
    setActive(null)
    activeId.current = null
    wantedId.current = null
    rememberConversationId(null)
    setPrompt("")
    setNotice(null)
    syncConversationUrl(null)
  }

  function openConversation(conversation: AiConversation) {
    applyConversation(conversation)
    setNotice(null)
    syncConversationUrl(conversation.id)
  }

  return (
    <AppShell eyebrow="Composer" title="Give it a title. Get a full private draft." wide>
      <div className="mb-4 flex md:hidden">
        <Button className="w-full rounded-xl" onClick={startNewChat}>
          <MessageSquarePlus data-icon="inline-start" />
          New chat
        </Button>
      </div>
      <div className="grid gap-4 xl:grid-cols-[14rem_minmax(0,1fr)_20rem] 2xl:grid-cols-[15rem_minmax(42rem,1fr)_22rem] 2xl:gap-6">
        <aside className="order-3 hidden rounded-3xl border bg-card p-4 shadow-sm xl:order-1 xl:block">
          <Button
            className="w-full rounded-xl"
            onClick={startNewChat}
          >
            <MessageSquarePlus data-icon="inline-start" />
            New draft
          </Button>
          <p className="mt-5 px-1 text-[11px] font-medium tracking-[0.14em] text-muted-foreground uppercase">Your Composer chats</p>
          <div className="mt-2 space-y-1">
            {conversations.length === 0 ? <p className="px-2 py-4 text-sm text-muted-foreground">No chats yet.</p> : null}
            {conversations.map((conversation) => (
              <button
                key={conversation.id}
                type="button"
                onClick={() => openConversation(conversation)}
                className={`w-full rounded-xl px-3 py-2 text-left text-sm transition-colors ${active?.id === conversation.id ? "bg-primary/10 text-foreground" : "hover:bg-muted"}`}
              >
                <span className="block truncate font-medium">{conversation.title || "Untitled chat"}</span>
                <span className="mt-1 block text-xs text-muted-foreground">
                  {conversation.is_generating ? "Writing…" : new Date(conversation.updated_at).toLocaleDateString()}
                </span>
              </button>
            ))}
          </div>
        </aside>

        <aside className="order-1 xl:sticky xl:top-24 xl:order-3 xl:self-start">
          <FeaturedImagePanel
            key={`${active?.id ?? "new"}-${active?.post?.id ?? "pending"}`}
            post={active?.post ?? null}
            query={active?.title || prompt}
            initialSuggestions={suggestions}
            allowMultiple
            onUpdated={(post: Post) => {
              if (!active) return
              setActive({ ...active, post })
            }}
            onNotice={setNotice}
            onSuggestions={(items: ImageSuggestion[]) => {
              if (!active) return
              setActive({ ...active, suggested_images: items })
            }}
          />
        </aside>

        <section className="order-2 min-w-0 rounded-3xl border bg-card shadow-sm xl:order-2">
          <div className="flex items-center justify-between border-b px-5 py-4">
            <div className="flex items-center gap-2">
              <span className="flex size-9 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <Wand2 className="size-4" />
              </span>
              <div>
                <p className="font-medium">{active?.title || "New Composer draft"}</p>
                <p className="text-xs text-muted-foreground">Private until you publish. Composer never goes live on its own.</p>
              </div>
            </div>
            {active ? (
              <button
                type="button"
                onClick={() => void archive()}
                className="app-icon-button"
                aria-label="Archive chat"
                disabled={pending || Boolean(active.is_generating)}
              >
                <Archive className="size-4" />
              </button>
            ) : null}
          </div>
          <div className="min-h-[22rem] space-y-5 p-3 sm:p-5 lg:p-6">
            {!active && !pending ? (
              <div className="rounded-2xl border border-dashed bg-muted/30 p-6 text-sm text-muted-foreground">
                Start with a title. Composer writes a detailed private blog, attaches two or three live photos, and you open the editor when you are ready.
              </div>
            ) : null}
            {active?.messages
              .filter((message) => message.role === "user" || message.content.trim())
              .map((message, _index, visible) => {
                const lastAssistant = [...visible].reverse().find((item) => item.role === "assistant")
                const showPost = message.role === "assistant" && lastAssistant?.id === message.id
                return (
              <div
                key={message.id}
                className={`text-sm leading-7 ${message.role === "user" ? "ml-auto max-w-3xl rounded-2xl bg-primary p-4 text-primary-foreground sm:p-5" : "w-full px-1 py-2"}`}
              >
                <p className="mb-2 text-[10px] font-medium tracking-[0.14em] uppercase opacity-70">
                  {message.role === "user" ? "You" : "Composer"}
                </p>
                {message.role === "assistant" ? (
                  <ComposerAnswer content={message.content} post={showPost ? active.post : null} />
                ) : (
                  <div className="whitespace-pre-wrap">{message.content}</div>
                )}
              </div>
                )
              })}
            {pending || active?.is_generating ? (
              <div className="space-y-3">
                <AiPipeline steps={COMPOSE_PIPELINE} />
                <p className="text-xs text-muted-foreground">Composer is writing a private draft. You can switch pages — this chat keeps generating and stores the draft when it finishes.</p>
              </div>
            ) : null}
            {notice ? (
              <p role="status" className="rounded-xl border border-destructive/30 bg-destructive/8 px-3 py-2 text-sm">
                {notice}
              </p>
            ) : null}
          </div>
          <form onSubmit={send} className="sticky bottom-0 border-t bg-card/95 p-3 pb-[calc(0.75rem+env(safe-area-inset-bottom,0px))] backdrop-blur sm:p-4 sm:pb-4">
            <label className="sr-only" htmlFor="composer-message">
              Message Composer
            </label>
            <textarea
              id="composer-message"
              className="editor-input min-h-20 resize-y"
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              maxLength={8000}
              placeholder={active ? "Ask for a rewrite, more detail, or a different section…" : "Give Composer a title…"}
            />
            <div className="mt-3 flex items-center justify-between gap-3">
              {active?.post ? (
                <Link className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline" href={`/editor/${active.post.id}`}>
                  <FileText className="size-4" />
                  Open in editor
                </Link>
              ) : (
                <span className="text-xs text-muted-foreground">The draft stays private.</span>
              )}
              <Button type="submit" disabled={pending || active?.is_generating || !prompt.trim()} className="rounded-xl">
                {pending || active?.is_generating ? <Sparkles className="size-4 animate-pulse" /> : <Send className="size-4" />}
                {pending || active?.is_generating ? "Writing" : active ? "Continue" : "Write draft"}
              </Button>
            </div>
          </form>
        </section>

      </div>
    </AppShell>
  )
}
