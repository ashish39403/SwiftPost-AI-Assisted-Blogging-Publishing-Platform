import { Suspense } from "react"
import { AnnaPage } from "@/features/app/anna-page"

export const metadata = { title: "Anna" }

export default function Page() {
  return (
    <Suspense fallback={<main className="grid min-h-dvh place-items-center text-sm text-muted-foreground">Opening Anna…</main>}>
      <AnnaPage />
    </Suspense>
  )
}
