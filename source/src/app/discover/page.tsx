import { Suspense } from "react"
import { DiscoverPage } from "@/features/public-blog/discover-page"

export const metadata = { title: "Discover" }

export default function Page() {
  return (
    <Suspense fallback={<main className="mx-auto w-full max-w-7xl px-5 py-14 text-sm text-muted-foreground">Loading stories…</main>}>
      <DiscoverPage />
    </Suspense>
  )
}
