import { Feather } from "lucide-react"
import { cn } from "cn"

export function Logo({ className }: { className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-2 font-semibold tracking-tight", className)}>
      <Feather aria-hidden="true" className="size-5 text-primary" />
      SwiftPost
    </span>
  )
}
