import { LandingPage } from "@/features/public-blog/landing-page"
import { LandingScrollReset } from "@/features/public-blog/landing-scroll-reset"

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"

const structuredData = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: "SwiftPost",
  url: siteUrl,
  description:
    "A publishing desk where authors research with Anna, review sources, and publish only after they confirm the story.",
}

export default function Home() {
  return (
    <main id="content">
      <LandingScrollReset />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
      />
      <LandingPage />
    </main>
  )
}
