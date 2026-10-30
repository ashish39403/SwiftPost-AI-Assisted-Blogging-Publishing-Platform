import { Suspense } from "react"
import { PublishedPage } from "@/features/app/published-page"

export const metadata = { title: "Published" }

export default function Page() {
  return (
    <Suspense fallback={<main className="grid min-h-dvh place-items-center text-sm text-muted-foreground">Opening published stories…</main>}>
      <PublishedPage />
    </Suspense>
  )
}
