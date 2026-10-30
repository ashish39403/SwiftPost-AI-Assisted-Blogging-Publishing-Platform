import Link from "next/link"
import { Logo } from "@/features/public-blog/logo"

const links = [
  { href: "/discover", label: "Discover" },
  { href: "/#authors", label: "For Authors" },
  { href: "/#how-it-works", label: "How It Works" },
  { href: "/#capabilities", label: "Help" },
]

export function SiteFooter() {
  return (
    <footer className="border-t">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-5 py-8 md:flex-row md:items-center md:px-8">
        <div className="flex flex-col gap-1">
          <Logo />
          <p className="text-xs text-muted-foreground">Real ideas. A brighter tomorrow.</p>
        </div>
        <nav aria-label="Footer" className="flex flex-wrap gap-x-5 gap-y-2 md:ml-auto">
          {links.map((link) => (
            <Link
              key={link.label}
              href={link.href}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
      <p className="mx-auto w-full max-w-7xl px-5 pb-6 text-xs text-muted-foreground md:px-8">
          SwiftPost keeps research, writing, and author approval connected in one publishing workflow.
      </p>
    </footer>
  )
}
