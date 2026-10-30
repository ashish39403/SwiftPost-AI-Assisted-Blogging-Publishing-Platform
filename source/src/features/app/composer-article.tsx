"use client"

import { mediaUrl, type FeaturedImage, type Post } from "@/lib/api"

type ArticleBlock =
  | { type: "heading"; text: string }
  | { type: "paragraph"; text: string }
  | { type: "list"; items: string[] }

type ParsedArticle = {
  title: string
  excerpt: string
  blocks: ArticleBlock[]
}

function takeLabeled(content: string) {
  const lines = content.replace(/\r\n/g, "\n").split("\n")
  let title = ""
  let excerpt = ""
  let mode: "start" | "excerpt" | "body" = "start"
  const body: string[] = []
  for (const line of lines) {
    const stripped = line.trim()
    const upper = stripped.toUpperCase()
    if (upper.startsWith("TITLE:")) {
      title = stripped.slice(stripped.indexOf(":") + 1).trim()
      mode = "start"
      continue
    }
    if (upper.startsWith("EXCERPT:")) {
      excerpt = stripped.slice(stripped.indexOf(":") + 1).trim()
      mode = "excerpt"
      continue
    }
    if (upper === "BODY:" || upper.startsWith("BODY:")) {
      const leftover = stripped.includes(":") ? stripped.slice(stripped.indexOf(":") + 1).trim() : ""
      mode = "body"
      if (leftover) body.push(leftover)
      continue
    }
    if (mode === "excerpt" && stripped) {
      excerpt = excerpt ? `${excerpt} ${stripped}` : stripped
      continue
    }
    body.push(line)
  }
  return { title, excerpt, body: body.join("\n").trim() }
}

function isHeading(line: string) {
  const text = line.trim()
  if (!text) return false
  if (/^#{1,3}\s+\S/.test(text)) return true
  if (/^[-*•]\s+/.test(text) || /^\d+[.)]\s+/.test(text)) return false
  if (/[.!?:]$/.test(text)) return false
  if (text.length < 8 || text.length > 72) return false
  const words = text.split(/\s+/)
  if (words.length < 2 || words.length > 10) return false
  return /^[\p{Lu}\p{Nd}"'][\p{L}\p{Nd}'’\-:, ]+$/u.test(text)
}

function parseBlocks(body: string): ArticleBlock[] {
  const blocks: ArticleBlock[] = []
  let list: string[] = []

  const flushList = () => {
    if (!list.length) return
    blocks.push({ type: "list", items: list })
    list = []
  }

  for (const raw of body.split("\n")) {
    const line = raw.trim()
    if (!line) {
      flushList()
      continue
    }
    const bullet = line.match(/^[-*•]\s+(.+)/)
    if (bullet) {
      list.push(bullet[1].trim())
      continue
    }
    flushList()
    const heading = line.replace(/^#{1,3}\s+/, "").trim()
    if (isHeading(line)) {
      blocks.push({ type: "heading", text: heading })
    } else {
      blocks.push({ type: "paragraph", text: line })
    }
  }
  flushList()
  return blocks
}

function parseComposerDisplay(content: string, post?: Post | null): ParsedArticle {
  const labeled = takeLabeled(content)
  const title = post?.title?.trim() || labeled.title
  const excerpt = post?.excerpt?.trim() || labeled.excerpt
  const body = post?.body?.trim() || labeled.body || content.trim()
  return { title, excerpt, blocks: parseBlocks(body) }
}

function extras(post?: Post | null): FeaturedImage[] {
  if (!post?.images?.length) return []
  const featuredId = post.featured_image?.id
  return post.images.filter((image) => image.id !== featuredId)
}

export function ComposerAnswer({ content, post }: { content: string; post?: Post | null }) {
  const article = parseComposerDisplay(content, post)
  const hero = post?.featured_image ?? null
  const gallery = extras(post)
  let extraIndex = 0
  let headingCount = 0

  if (!article.title && !article.excerpt && article.blocks.length === 0) {
    return <p className="whitespace-pre-wrap text-[15px] leading-7 text-foreground">{content}</p>
  }

  return (
    <article className="composer-article">
      {article.title ? <h1>{article.title}</h1> : null}
      {article.excerpt ? <p className="composer-lead">{article.excerpt}</p> : null}
      {hero ? (
        <figure className="composer-hero">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={mediaUrl(hero.url)} alt="" />
        </figure>
      ) : null}
      {article.blocks.map((block, index) => {
        const nodes = []
        if (block.type === "heading") {
          headingCount += 1
          nodes.push(
            <h2 key={`h-${index}`}>{block.text}</h2>,
          )
          if (headingCount === 3 && gallery[extraIndex]) {
            const image = gallery[extraIndex]
            extraIndex += 1
            nodes.push(
              <figure key={`img-${image.id}`} className="composer-inline">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={mediaUrl(image.url)} alt="" />
              </figure>,
            )
          }
        } else if (block.type === "list") {
          nodes.push(
            <ul key={`l-${index}`}>
              {block.items.map((item, itemIndex) => (
                <li key={`${index}-${itemIndex}`}>{item}</li>
              ))}
            </ul>,
          )
        } else {
          nodes.push(
            <p key={`p-${index}`}>{block.text}</p>,
          )
        }
        return nodes
      })}
      {gallery.slice(extraIndex).length ? (
        <div className="composer-gallery">
          {gallery.slice(extraIndex).map((image) => (
            <figure key={image.id}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={mediaUrl(image.url)} alt="" />
            </figure>
          ))}
        </div>
      ) : null}
    </article>
  )
}
