export const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? ""

/** How long the UI waits for Composer/Anna after the first request drops. */
export const AI_WAIT_MS = 270_000

export function sleep(ms: number) {
  return new Promise<void>((resolve) => {
    window.setTimeout(resolve, ms)
  })
}

export function isRetryableAiStatus(status: number) {
  return status === 408 || status >= 500
}

export function mediaUrl(url: string | null | undefined) {
  if (!url) return ""
  if (/^(https?:|data:|blob:)/i.test(url)) return url
  const base = apiUrl.replace(/\/$/, "")
  return `${base}${url.startsWith("/") ? url : `/${url}`}`
}

export type Account = {
  id: number
  username: string
  email: string
  role: "reader" | "author" | "admin"
  first_name: string
  last_name: string
}

export type Category = {
  id: number
  name: string
  slug: string
  description?: string
  is_active?: boolean
}

export type FeaturedImage = {
  id: number
  post_id: number
  content_type: string
  byte_size: number
  width: number
  height: number
  original_filename: string
  url: string
}

export type ImageSuggestion = {
  id: number
  image_url: string
  page_url: string
  description: string
  selected?: boolean
  retrieved_at: string
}

export type CommentItem = {
  id: number
  post_id: number
  author: { id: number; username: string }
  body: string
  status: string
  created_at: string
}

export type Post = {
  id: number
  title: string
  slug: string
  excerpt: string
  body: string
  status: string
  category: { id: number; name: string; slug: string } | null
  author: { id: number; username: string }
  featured_image: FeaturedImage | null
  images: FeaturedImage[]
  like_count: number
  comment_count: number
  liked: boolean
  published_at: string | null
  created_at: string
  updated_at: string
}

export type Paginated<T> = {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export type ConversationMessage = {
  id: string
  role: "user" | "assistant" | "tool"
  content: string
  sequence: number
  created_at: string
}

export type AiConversation = {
  id: string
  title: string
  status: "active" | "archived"
  post: Post | null
  messages: ConversationMessage[]
  is_generating?: boolean
  last_error?: string
  suggested_images?: ImageSuggestion[]
  created_at: string
  updated_at: string
}

type ErrorEnvelope = {
  error?: {
    message?: string
    details?: Record<string, string | string[]>
  }
}

let csrfToken: string | null = null
const TAB_SESSION_KEY = "swiftpost.tabSession"

export function accountHome(role: Account["role"]) {
  return role === "reader" ? "/discover" : "/dashboard"
}

export function accountLabel(account: Account) {
  const name = `${account.first_name} ${account.last_name}`.trim()
  return name || account.username
}

function tabSessionKey() {
  if (typeof window === "undefined") return null
  try {
    return window.sessionStorage.getItem(TAB_SESSION_KEY)
  } catch {
    return null
  }
}

function rememberTabSession(response: Response) {
  const key = response.headers.get("X-Session-Key")
  if (!key || typeof window === "undefined") return
  try {
    window.sessionStorage.setItem(TAB_SESSION_KEY, key)
  } catch {
    return
  }
}

export function clearTabSession() {
  csrfToken = null
  if (typeof window === "undefined") return
  try {
    window.sessionStorage.removeItem(TAB_SESSION_KEY)
  } catch {
    return
  }
}

function withTabSession(headers: Headers) {
  const key = tabSessionKey()
  if (key) headers.set("X-Session-Key", key)
  return headers
}

export async function api(path: string, init: RequestInit = {}, retry = true) {
  const headers = withTabSession(new Headers(init.headers))
  const method = (init.method ?? "GET").toUpperCase()
  if (method !== "GET" && method !== "HEAD") {
    headers.set("X-CSRFToken", await ensureCsrf())
  }
  if (init.body && !headers.has("Content-Type") && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json")
  }
  const response = await fetch(`${apiUrl}${path}`, {
    ...init,
    headers,
    credentials: "include",
  })
  rememberTabSession(response)
  if (path.includes("/auth/logout/") && response.ok) {
    clearTabSession()
  }
  if (response.status === 403 && retry && method !== "GET") {
    csrfToken = null
    return api(path, init, false)
  }
  return response
}

export async function readError(response: Response, fallback: string) {
  try {
    const body = (await response.json()) as ErrorEnvelope
    const details = body.error?.details ?? {}
    const first = Object.values(details)[0]
    if (Array.isArray(first) && first[0]) return String(first[0])
    if (typeof first === "string" && first) return first
    return body.error?.message || fallback
  } catch {
    return fallback
  }
}

async function ensureCsrf() {
  if (csrfToken) return csrfToken
  const headers = withTabSession(new Headers())
  const response = await fetch(`${apiUrl}/api/v1/auth/csrf/`, { credentials: "include", headers })
  rememberTabSession(response)
  if (!response.ok) throw new Error("Could not start a secure session.")
  const body = (await response.json()) as { csrfToken?: string }
  if (!body.csrfToken) throw new Error("Could not start a secure session.")
  csrfToken = body.csrfToken
  return csrfToken
}
