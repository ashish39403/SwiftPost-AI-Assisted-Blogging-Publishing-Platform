import { Suspense } from "react"
import { PostPage } from "@/features/public-blog/post-page"

export default function Page({ params }: { params: Promise<{ slug: string }> }) {
  return (
    <Suspense fallback={<main id="content" className="mx-auto w-full max-w-3xl px-5 py-16 text-sm text-muted-foreground md:px-8">Loading story…</main>}>
      <PostFromParams params={params} />
    </Suspense>
  )
}

async function PostFromParams({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  return <PostPage slug={slug} />
}
