import { Suspense } from "react"
import { EditorPage } from "@/features/app/editor-page"

export default function Page({ params }: { params: Promise<{ id: string }> }) {
  return (
    <Suspense fallback={<main className="grid min-h-dvh place-items-center text-sm text-muted-foreground">Opening editor…</main>}>
      <EditorFromParams params={params} />
    </Suspense>
  )
}

async function EditorFromParams({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  return <EditorPage postId={id} />
}
