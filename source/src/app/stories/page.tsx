import { Suspense } from "react"
import { StoriesPage } from "@/features/app/stories-page"

export const metadata = { title: "Stories" }

export default function Page() {
  return (
    <Suspense fallback={<main className="grid min-h-dvh place-items-center text-sm text-muted-foreground">Opening stories…</main>}>
      <StoriesPage />
    </Suspense>
  )
}
