import { Suspense } from "react"
import { ComposePage } from "@/features/app/compose-page"

export const metadata = { title: "Composer" }

export default function Page() {
  return (
    <Suspense fallback={<main className="grid min-h-dvh place-items-center text-sm text-muted-foreground">Opening Composer…</main>}>
      <ComposePage />
    </Suspense>
  )
}
